#!/usr/bin/env node
// OpenAI text-to-speech. Text in, one audio file out.
//
//   node tts.mjs narration.txt narration.mp3 [--voice sage] [--model gpt-4o-mini-tts]
//                                            [--instructions "..."] [--speed 1]
//
// The engine speaks HeyGen, ElevenLabs and Kokoro, not OpenAI; ADR-0005 chooses
// OpenAI anyway, and this adapter is the whole of that choice. Route every voice
// track through it and add no second path.
//
// The key is OPENAI_API_KEY in .env beside this file and nowhere else - this repo
// is public. One request, one file: narration for a video is generated in a single
// pass (ADR-0003).

import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const [input, output, ...flags] = process.argv.slice(2);
if (!input || !output) {
  console.error("usage: node tts.mjs <text-file> <out.mp3> [--voice v] [--model m] [--instructions s] [--speed n]");
  process.exit(2);
}
const opt = (name, fallback) => {
  const i = flags.indexOf(`--${name}`);
  return i === -1 ? fallback : flags[i + 1];
};

process.loadEnvFile(join(dirname(fileURLToPath(import.meta.url)), ".env"));
if (!process.env.OPENAI_API_KEY) {
  console.error("OPENAI_API_KEY is not set in .env");
  process.exit(2);
}

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
    speed: Number(opt("speed", 1)),
    response_format: "mp3",
  }),
});

if (!response.ok) {
  console.error(`openai ${response.status}: ${await response.text()}`);
  process.exit(1);
}

writeFileSync(output, Buffer.from(await response.arrayBuffer()));
console.error(`wrote ${output}`);
