"""usage: python3 transcribe_many.py <model> <out_dir> file1 file2 ...  -> <out_dir>/<stem>.json (word timestamps)"""
import sys, json, subprocess, os
import numpy as np
from faster_whisper import WhisperModel
model, out = sys.argv[1], sys.argv[2]
m = WhisperModel(model, device="cpu", compute_type="int8", cpu_threads=4)
for f in sys.argv[3:]:
    pcm = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"], capture_output=True, check=True).stdout, np.float32)
    segs, info = m.transcribe(pcm, language="pt", word_timestamps=True, beam_size=5, vad_filter=False,
                              initial_prompt="MRTI, CNAE, DAS, CAC, markup, margem bruta, 13º salário, convenção coletiva, fluxo de caixa.")
    res = []
    stem = os.path.splitext(os.path.basename(f))[0]
    for s in segs:
        res.append({"start": s.start, "end": s.end, "text": s.text, "words": [{"w": w.word, "s": w.start, "e": w.end, "p": w.probability} for w in s.words]})
        print(f"{stem} [{s.start:6.2f}-{s.end:6.2f}] {s.text}", flush=True)
    json.dump(res, open(os.path.join(out, stem + ".json"), "w"), ensure_ascii=False, indent=1)
print("ALL DONE", flush=True)
