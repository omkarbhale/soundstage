#!/usr/bin/env node
// Text to speech. Text in, one audio file out, one path for every voice track.
//
//   node tts.mjs narration.txt narration.mp3 [--engine auto|openai|kokoro]
//                [--voice sage] [--model gpt-4o-mini-tts] [--instructions "..."]
//                [--speed 1]
//
// TWO ENGINES BEHIND ONE PATH. ADR-0005 chose OpenAI and this adapter is the
// whole of that choice; ADR-0009 adds local Kokoro beside it, which the engine
// speaks natively - so the Kokoro path SHELLS OUT TO THE ENGINE rather than
// reimplementing it (ADR-0001). Add no third path and no second caller.
//
//   auto    OpenAI when a key is present, falling back to Kokoro - loudly - when
//           the key is refused or out of credit. Never silent: the engine that
//           actually spoke is always printed.
//   openai  OpenAI only. Fails rather than substituting a different voice.
//   kokoro  Local only. No key, no network, no account.
//
// --lexicon is a respelling table for the Kokoro path only, because a local model
// has no `instructions` control and gets proper nouns wrong: measured here, it
// read "Aras" as ARR-as and "tas-playwright" as "task playwright". Respelling the
// INPUT fixes the sound without touching the script the guards check, so
// verify.py still diffs the real narration against the real audio. OpenAI does
// not use it - it says these correctly already.
//
// The key is OPENAI_API_KEY in .env beside this file and nowhere else - this repo
// is public. Kokoro needs HYPERFRAMES_PYTHON pointing at a Python that has
// `kokoro-onnx` and `soundfile` (README, "Speaking without an account").
// One request, one file: narration for a video is generated in a single pass
// (ADR-0003).

import { readFileSync, writeFileSync, existsSync, mkdtempSync, rmSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { tmpdir } from "node:os";

const [input, output, ...flags] = process.argv.slice(2);
if (!input || !output) {
  console.error("usage: node tts.mjs <text-file> <out.mp3> [--engine auto|openai|kokoro] [--voice v] [--model m] [--instructions s] [--speed n] [--lexicon respellings.json]");
  process.exit(2);
}
const opt = (name, fallback) => {
  const i = flags.indexOf(`--${name}`);
  return i === -1 ? fallback : flags[i + 1];
};

const here = dirname(fileURLToPath(import.meta.url));
if (existsSync(join(here, ".env"))) process.loadEnvFile(join(here, ".env"));

const engine = opt("engine", "auto");
if (!["auto", "openai", "kokoro"].includes(engine)) {
  console.error(`unknown --engine ${engine}: use auto, openai or kokoro`);
  process.exit(2);
}
const speed = Number(opt("speed", 1));

// ---------------------------------------------------------------- OpenAI
async function openai() {
  if (!process.env.OPENAI_API_KEY) return { ok: false, why: "OPENAI_API_KEY is not set in .env" };
  const response = await fetch("https://api.openai.com/v1/audio/speech", {
    method: "POST",
    headers: {
      authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
      "content-type": "application/json",
    },
    body: JSON.stringify({
      model: opt("model", "gpt-4o-mini-tts"),
      voice: opt("voice", "sage"),
      input: readFileSync(input, "utf8"),
      instructions: opt("instructions", undefined),
      speed,
      response_format: "mp3",
    }),
  });
  if (!response.ok) return { ok: false, why: `openai ${response.status}: ${await response.text()}` };
  writeFileSync(output, Buffer.from(await response.arrayBuffer()));
  return { ok: true };
}

// ---------------------------------------------------------------- Kokoro
// The engine owns this model. We call its `tts` command and convert the wav it
// writes; nothing here loads a model or touches kokoro-onnx directly.
function kokoro() {
  const voice = opt("voice", "bf_emma");
  if (opt("instructions", undefined) !== undefined) {
    console.error("note: --instructions is an OpenAI-only control; Kokoro has no equivalent and it is being ignored.");
  }
  const tmp = mkdtempSync(join(tmpdir(), "tts-"));
  const wav = join(tmp, "speech.wav");
  let spoken = input;
  try {
    const lex = opt("lexicon", undefined);
    if (lex !== undefined) {
      if (!existsSync(lex)) return { ok: false, why: `no such lexicon: ${lex}` };
      const table = JSON.parse(readFileSync(lex, "utf8"));
      let text = readFileSync(input, "utf8");
      let applied = 0;
      for (const [written, say] of Object.entries(table)) {
        // Whole word only: respelling "Aras" must not reach inside an identifier
        // that happens to contain it.
        const re = new RegExp(`(?<![\\w-])${written.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}(?![\\w-])`, "g");
        text = text.replace(re, () => { applied++; return say; });
      }
      spoken = join(tmp, "spoken.txt");
      writeFileSync(spoken, text);
      console.error(`lexicon: ${applied} respelling(s) applied before synthesis`);
    }
    const version = process.env.HYPERFRAMES_VERSION || "0.8.12";
    const r = spawnSync("npx", ["--yes", `hyperframes@${version}`, "tts",
      "--text-file", spoken, "-o", wav, "--voice", voice, "--speed", String(speed)],
      { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] });
    if (r.status !== 0 || !existsSync(wav)) {
      const hint = /kokoro_onnx|Python 3 is required|not installed/i.test(`${r.stdout}${r.stderr}`)
        ? "\nKokoro needs a Python with kokoro-onnx and soundfile. Point HYPERFRAMES_PYTHON at it (README, \"Speaking without an account\")."
        : "";
      return { ok: false, why: `hyperframes tts failed:\n${(r.stderr || r.stdout || "").trim()}${hint}` };
    }
    // The rest of the chain reads mp3, so convert rather than teach every caller
    // about a second container.
    const f = spawnSync("ffmpeg", ["-v", "error", "-y", "-i", wav, "-c:a", "libmp3lame", "-q:a", "2", output],
      { encoding: "utf8" });
    if (f.status !== 0) return { ok: false, why: `ffmpeg failed converting the wav:\n${(f.stderr || "").trim()}` };
    return { ok: true };
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
}

// ---------------------------------------------------------------- dispatch
function quotaRefusal(why) {
  return /insufficient_quota|credit_balance_exhausted|no credits remaining|\b401\b|invalid_api_key/i.test(why);
}

let used, result;
if (engine === "kokoro") {
  used = "kokoro"; result = kokoro();
} else {
  used = "openai"; result = await openai();
  if (!result.ok && engine === "auto") {
    console.error(`openai refused, falling back to local Kokoro:\n${result.why}`);
    if (!quotaRefusal(result.why)) console.error("(the refusal was not about credit - worth reading before trusting this audio)");
    used = "kokoro"; result = kokoro();
  }
}
if (!result.ok) {
  console.error(result.why);
  process.exit(1);
}
console.error(`wrote ${output} [engine: ${used}]`);
