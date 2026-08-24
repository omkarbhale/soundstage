# The end of speech, measured - the number the closing hold is built from.
#
# House style asks for a closing card that holds about two seconds past the last
# word and then ends, and for that measurement to be measured rather than guessed.
# The obvious way to take it is wrong in a way that fails silently: silencedetect
# reports the START of each silence, so the last silence_start is the end of speech
# only if the file actually ends in silence. Module 7's narration ended on its final
# word with 0.2s of file left, so nothing trailing was detected and the last
# silence_start was a pause six seconds earlier, mid-script. A hold built on that
# number leaves the closing card sitting there in silence - which is module 1's
# defect, arrived at from the other direction.
#
# So this refuses to answer unless the file ends in a silence it can measure to.
# Give the voice track a tail before measuring (ffmpeg apad, which is wanted anyway
# so the last word can decay instead of stopping dead).
#
#   python3 speech_end.py voice.mp3
#
# Prints the end of speech in seconds. Exits non-zero, saying why, when the file
# ends mid-speech and the honest answer is that it cannot be measured.
import re, subprocess, sys

PATH = sys.argv[1]
NOISE, MIN = "-45dB", 0.35        # a silence shorter than this is a breath, not an end
TAIL = 0.15                       # sound continuing past the last silence by more than this = ends mid-speech

def ffmpeg_stderr(*af):
    return subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", PATH,
                           *af, "-f", "null", "-"], capture_output=True, text=True).stderr

dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "csv=p=0", PATH], capture_output=True, text=True).stdout)
out = ffmpeg_stderr("-af", f"silencedetect=noise={NOISE}:d={MIN}")
starts = [float(m) for m in re.findall(r"silence_start:\s*([\d.]+)", out)]
ends   = [float(m) for m in re.findall(r"silence_end:\s*([\d.]+)", out)]

if not starts:
    sys.exit(f"{PATH}: no silence at all at {NOISE} - nothing to measure the end of speech against")
# silencedetect closes the trailing silence at EOF as well, so "is there a
# silence_end?" proves nothing. What proves it is where that end sits: if sound
# resumed and ran on to the end of the file, the last silence_start is a pause
# inside the script and the file ends mid-speech.
if ends and dur - ends[-1] > TAIL:
    sys.exit(f"{PATH}: ends mid-speech - {dur - ends[-1]:.3f}s of sound runs to the end of the file. "
             f"The last silence_start ({starts[-1]:.3f}s) is a pause inside the script, not the end of speech. "
             f"Pad the tail (ffmpeg apad) so the last word can decay, and measure again.")
print(f"{starts[-1]:.3f}")
