"""Timeline for the 'computer screens' reel: opening -> pain windows -> MRTI turn -> offer -> CTA -> end card.

usage: python3 plan_screens.py <v5 dir> <timeline.json>
Reads <dir>/clips.json and the per-video transcripts <dir>/vN.json.
"""
import json
import re
import sys

D, OUT = sys.argv[1], sys.argv[2]
FPS = 30
CL = {name: (v, rs) for name, v, rs in json.load(open(f"{D}/clips.json"))}
TR = {}


def words_of(v):
    if v not in TR:
        TR[v] = [{"w": w["w"].strip(), "s": w["s"], "e": w["e"]} for s in json.load(open(f"{D}/{v}.json")) for w in s["words"]]
    return TR[v]


FIX = {"dizer?": "dizer?", "R$": "R$"}
# crop rectangles inside the 576x1024 source frame (fractions x0, y0, x1, y1)
CROP = {"c1": [0, 0.0, 1, 1.0], "c2": [0, 0.0, 1, 0.64], "c3": [0, 0.49, 1, 0.84], "c4": [0, 0.24, 1, 0.64], "c5": [0, 0.32, 1, 0.71],
        "c6": [0, 0.30, 1, 0.69], "c7": [0, 0.20, 1, 0.74], "c8": [0, 0.19, 1, 0.72], "c9": [0, 0.35, 1, 0.74], "c10": [0, 0.36, 1, 0.73]}
FILE = {"c1": "diretor_mrti.mp4", "c2": "faturamento_3_meses.mp4", "c3": "lucrei_10_mil.mp4", "c4": "margem_ou_markup.mp4",
        "c5": "processo_trabalhista.mp4", "c6": "caixa_13_salario.mp4", "c7": "voce_faz_tudo.mp4", "c8": "mrti.mp4", "c9": "mrti_solucoes.mp4",
        "c10": "chama_a_mrti.mp4"}
LABEL = {"c2": ("DOR 01", "Faturamento"), "c3": ("DOR 02", "Lucro"), "c4": ("DOR 03", "Precificação"), "c5": ("DOR 04", "Passivo trabalhista"),
         "c6": ("DOR 05", "Caixa"), "c7": ("DOR 06", "Sobrecarga")}

# ---------------- output placement ----------------
START = {"c1": 3.40}
order = ["c2", "c3", "c4", "c5", "c6", "c7"]
GAP = 0.16
clips = {}


def dur(name):
    return sum(b - a for a, b in CL[name][1])


t = 8.30                       # after the headline
START["c1"] = 3.40
for n in order:
    START[n] = round(t, 3); t += dur(n) + GAP
OVERLOAD = round(t - GAP + 0.05, 3)       # system overload + implode
t = OVERLOAD + 0.55
START["c8"] = round(t, 3); t += dur("c8") + 0.12
START["c9"] = round(t, 3); t += dur("c9") + 0.15
START["c10"] = round(t, 3); t += dur("c10")
VIDEO_END = round(t + 0.10, 3)
END_CARD = VIDEO_END
TOTAL = round(END_CARD + 4.0, 3)

segments = []                  # audio/frames: (clip, src_a, src_b, out_start)
for name in ["c1"] + order + ["c8", "c9", "c10"]:
    v, rs = CL[name]
    o = START[name]; local = 0.0; parts = []
    for a, b in rs:
        segments.append({"clip": name, "video": v, "src_start": a, "src_end": b, "out_start": round(o, 3), "out_end": round(o + b - a, 3), "local": round(local, 3)})
        parts.append([a, b, round(local, 3)])
        o += b - a; local += b - a
    clips[name] = {"video": v, "start": START[name], "dur": round(local, 3), "parts": parts, "crop": CROP[name], "file": FILE[name],
                   "label": LABEL.get(name), "nframes": int(round(local * FPS))}


def out_t(name, src):
    for a, b, loc in clips[name]["parts"]:
        if a - 0.05 <= src <= b + 0.05:
            return round(START[name] + loc + min(max(src, a), b) - a, 3)
    return None


# ---------------- captions ----------------
caps = []
KEY = {"rico", "dublê", "faturamento", "lucrando", "lucrei", "funcionário", "luz", "errou", "margem", "lucro", "150%", "errado", "multa",
       "correção", "monetária", "juros", "capital", "giro", "fluxo", "caixa", "aguenta", "preparado", "tudo", "financeiro", "rh", "departamento",
       "pessoal", "energia", "mrti", "processo", "valiosa", "dinheiro", "especialistas", "soluções", "números", "dados", "consultoria",
       "empresarial", "sabe", "13º", "10", "mil"}
for name in ["c1"] + order + ["c8", "c9", "c10"]:
    v, rs = CL[name]
    ws = []
    for w in words_of(v):
        mid = (w["s"] + w["e"]) / 2
        if any(a - 0.02 <= mid <= b + 0.02 for a, b in rs):
            o0, o1 = out_t(name, w["s"]), out_t(name, w["e"])
            if o0 is None:
                continue
            txt = w["w"]
            txt = re.sub(r"^R\$", "R$ ", txt)
            ws.append({"w": txt, "s": o0, "e": max(o1 or o0, o0 + 0.08)})
    # merge whisper's split number/percent tokens
    m = []
    for w in ws:
        if m and (w["w"] in ("%", "%?", "%.", "%,") or (m[-1]["w"].isdigit() and w["w"] == "mil.")):
            m[-1]["w"] += w["w"] if w["w"].startswith("%") else " " + w["w"]; m[-1]["e"] = w["e"]; continue
        m.append(dict(w))
    chunk = []
    for k in m:
        if chunk and (k["s"] - chunk[-1]["e"] > 0.3 or len(chunk) >= 3 or sum(len(x["w"]) for x in chunk) + len(k["w"]) > 17):
            caps.append(chunk); chunk = []
        chunk.append(k)
        if re.search(r"[.?!]$", k["w"]) or (k["w"].endswith(",") and len(chunk) >= 2):
            caps.append(chunk); chunk = []
    if chunk:
        caps.append(chunk)
cap_out = []
for i, c in enumerate(caps):
    nxt = caps[i + 1][0]["s"] if i + 1 < len(caps) else c[-1]["e"] + 0.5
    cap_out.append({"start": round(c[0]["s"] - 0.04, 3), "end": round(min(nxt, c[-1]["e"] + 0.3), 3),
                    "words": [{"w": x["w"].rstrip(".,!"), "s": x["s"], "e": x["e"], "key": x["w"].lower().strip(".,!?") in KEY,
                               "num": bool(re.search(r"\d", x["w"]))} for x in c]})

# ---------------- events ----------------
c1 = clips["c1"]
ev = {
    "c1Expand": out_t("c1", 2.70),          # "Não," -> the window goes full screen
    "c1Punch": out_t("c1", 3.04),           # "dublê"
    "head1": round(c1["start"] + c1["dur"] + 0.08, 3), "head2": round(c1["start"] + c1["dur"] + 0.70, 3),
    "overload": OVERLOAD, "turn": START["c8"],
    "processo": out_t("c8", 32.80),
    "six": out_t("c9", 40.96), "mods": [out_t("c9", 43.12), out_t("c9", 43.80), out_t("c9", 44.44), out_t("c9", 45.54)],
    "specialists": out_t("c9", 38.80), "chama": out_t("c10", 135.36),
    # widget beats inside each pain
    "w_c2": [out_t("c2", 36.10), out_t("c2", 37.66)],
    "w_c3": [out_t("c3", 68.72), out_t("c3", 69.48), out_t("c3", 70.66), out_t("c3", 71.92)],
    "w_c4": [out_t("c4", 38.52), out_t("c4", 39.22), out_t("c4", 40.74)],
    "w_c5": [out_t("c5", 67.32), out_t("c5", 68.36), out_t("c5", 69.72), out_t("c5", 72.42), out_t("c5", 73.30)],
    "w_c6": [out_t("c6", 5.52), out_t("c6", 6.94)],
    "w_c7": [out_t("c7", w) for w in (6.20, 7.08, 8.24, 16.46)],
}
tl = {"fps": FPS, "total": TOTAL, "videoEnd": VIDEO_END, "endCard": END_CARD, "clips": clips, "order": order, "segments": segments,
      "captions": cap_out, "ev": ev}
json.dump(tl, open(OUT, "w"), ensure_ascii=False, indent=1)
print(f"total {TOTAL}s  end card {END_CARD}  overload {OVERLOAD}  turn {START['c8']}")
for n in ["c1"] + order + ["c8", "c9", "c10"]:
    print(n, clips[n]["start"], clips[n]["dur"], clips[n]["file"])
print(json.dumps(ev))
