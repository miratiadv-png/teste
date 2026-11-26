"""Timeline v4 (clear offer): face hook -> burst + headline -> 3 pains -> overload -> turn ->
5 services one by one (Financeiro, RH, DP, Consultoria, Sistema) -> outcome -> free analysis -> end card.

usage: python3 plan_v4.py <v5 dir> <timeline.json> <clips_out.json>
"""
import json
import re
import sys

D, OUT, CLOUT = sys.argv[1], sys.argv[2], sys.argv[3]
FPS = 30
# clip id -> (video, parts in source seconds, crop, file name)
CL = {
    "c1": ("v2", [[0.55, 3.92]], [0, 0, 1, 1], "diretor_mrti.mp4"),
    "c3": ("v2", [[68.30, 72.70]], [0, 0.49, 1, 0.84], "lucrei_10_mil.mp4"),
    "c5": ("v6", [[66.30, 70.16]], [0, 0.32, 1, 0.71], "processo_trabalhista.mp4"),
    "c6": ("v4", [[4.50, 7.68]], [0, 0.30, 1, 0.69], "caixa_13_salario.mp4"),
    "t1": ("v5", [[28.50, 30.62]], [0, 0.19, 1, 0.72], "mrti.mp4"),
    "s1": ("v2", [[98.16, 104.14]], [0, 0.49, 1, 0.84], "financeiro.mp4"),
    "s2": ("v6", [[91.00, 93.62], [101.74, 104.68]], [0, 0.36, 1, 0.71], "departamento_pessoal.mp4"),
    "s3": ("v5", [[33.66, 36.02], [38.52, 40.22]], [0, 0.19, 1, 0.72], "rh.mp4"),
    "s4": ("v5", [[55.94, 58.32], [30.66, 33.40]], [0, 0.19, 1, 0.72], "consultoria.mp4"),
    "s5": ("v5", [[42.78, 44.98]], [0, 0.19, 1, 0.72], "sistema.mp4"),
    "oc": ("v5", [[47.30, 52.98]], [0, 0.12, 1, 0.72], "mrti_faz_por_voce.mp4"),
    "c12": ("v6", [[154.70, 158.66]], [0, 0.28, 1, 0.665], "analise_gratuita.mp4"),
}
LABEL = {"c3": ("DOR 01", "Lucro"), "c5": ("DOR 02", "Passivo trabalhista"), "c6": ("DOR 03", "Caixa")}
SVC = [
    ("s1", "Financeiro", "A gente assume o seu financeiro.", ["Contas a pagar e a receber", "Fluxo de caixa e conciliação bancária", "DRE e relatório mensal de resultado"],
     "Você sabe quanto lucrou de verdade, todo mês."),
    ("s3", "RH", "O time certo no lugar certo.", ["Recrutamento e seleção", "Cargos e salários", "Benefícios, ponto e clima"],
     "Uma equipe que funciona sem você em tudo."),
    ("s2", "Departamento pessoal", "Sua folha certa, do jeito da lei.", ["Folha de pagamento, férias e 13º", "Admissões e desligamentos", "Tudo conforme a convenção do sindicato"],
     "Menos risco de processo trabalhista."),
    ("s4", "Consultoria empresarial", "Planejamento e processo para crescer.", ["Diagnóstico completo da empresa", "Plano estratégico de crescimento", "Processos e organograma"],
     "Sua empresa cresce sem depender só de você."),
    ("s5", "Sistema de gestão", "Sua empresa inteira num só sistema.", ["Financeiro, RH e vendas integrados", "Implantação e treinamento da equipe", "Suporte e acompanhamento mensal"],
     "Números e dados num painel só."),
]
TR = {}


def words_of(v):
    if v not in TR:
        TR[v] = [{"w": w["w"].strip(), "s": w["s"], "e": w["e"]} for s in json.load(open(f"{D}/{v}.json")) for w in s["words"]]
    return TR[v]


def dur(n):
    return sum(b - a for a, b in CL[n][1])


START = {"c1": 0.0}
t = 6.35
order = ["c3", "c5", "c6"]
for n in order:
    START[n] = round(t, 3); t += dur(n) + 0.16
OVERLOAD = round(t - 0.16 + 0.05, 3)
t = OVERLOAD + 0.55
START["t1"] = round(t, 3); t += dur("t1") + 0.5
SVC_START = round(t, 3)
sections = []
for key, name, sub, tasks, outc in SVC:
    d = max(dur(key) + 0.9, 5.2)
    START[key] = round(t + 0.3, 3)
    sections.append({"key": key, "name": name, "sub": sub, "tasks": tasks, "out": outc, "start": round(t, 3), "end": round(t + d, 3)})
    t += d
OUTCOME = round(t, 3)
START["oc"] = round(t + 0.2, 3); t = START["oc"] + dur("oc") + 0.2
START["c12"] = round(t, 3); t += dur("c12")
VIDEO_END = round(t + 0.25, 3)
END_CARD = VIDEO_END
TOTAL = round(END_CARD + 5.0, 3)
SEQ = ["c1"] + order + ["t1"] + [x[0] for x in SVC] + ["oc", "c12"]

clips, segments = {}, []
for name in SEQ:
    v, rs, crop, file = CL[name]
    o = START[name]; local = 0.0; parts = []
    for a, b in rs:
        segments.append({"clip": name, "video": v, "src_start": a, "src_end": b, "out_start": round(o, 3), "out_end": round(o + b - a, 3), "local": round(local, 3)})
        parts.append([a, b, round(local, 3)]); o += b - a; local += b - a
    clips[name] = {"video": v, "start": START[name], "dur": round(local, 3), "parts": parts, "crop": crop, "file": file,
                   "label": LABEL.get(name), "nframes": int(round(local * FPS))}


def out_t(name, src):
    for a, b, loc in clips[name]["parts"]:
        if a - 0.05 <= src <= b + 0.05:
            return round(START[name] + loc + min(max(src, a), b) - a, 3)
    return None


KEY = {"rico", "dublê", "lucrei", "funcionário", "luz", "multa", "correção", "monetária", "juros", "caixa", "aguenta", "preparado",
       "mrti", "processo", "valiosa", "sistema", "dinheiro", "especialistas", "números", "dados", "margem", "líquida", "conta", "convenções",
       "planejamento", "vendas", "negócio", "operação", "realidade", "tudo", "energia", "13º", "10", "mil"}
caps = []
for name in SEQ:
    v, rs = CL[name][0], CL[name][1]
    ws = []
    for w in words_of(v):
        mid = (w["s"] + w["e"]) / 2
        if any(a - 0.02 <= mid <= b + 0.02 for a, b in rs):
            o0, o1 = out_t(name, w["s"]), out_t(name, w["e"])
            if o0 is None:
                continue
            ws.append({"w": w["w"], "s": o0, "e": max(o1 or o0, o0 + 0.08)})
    ws.sort(key=lambda x: x["s"])
    chunk = []
    for k in ws:
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

c1end = clips["c1"]["dur"]
ev = {
    "c1Punch": out_t("c1", 3.04), "burst": round(c1end, 3), "h1": round(c1end + 1.05, 3), "h2": round(c1end + 1.55, 3), "h3": round(c1end + 2.10, 3),
    "overload": OVERLOAD, "turn": START["t1"], "svc": SVC_START, "outcome": OUTCOME,
    "chama": out_t("c12", 154.78), "ajustar": out_t("c12", 155.80), "entender": out_t("c12", 157.04),
    "w_c3": [out_t("c3", 68.72), out_t("c3", 69.48), out_t("c3", 70.66), out_t("c3", 71.92)],
    "w_c5": [out_t("c5", 67.32), out_t("c5", 68.36), out_t("c5", 69.72)],
    "w_c6": [out_t("c6", 5.52), out_t("c6", 6.94)],
}
tl = {"fps": FPS, "total": TOTAL, "videoEnd": VIDEO_END, "endCard": END_CARD, "clips": clips, "order": order, "seq": SEQ,
      "sections": sections, "segments": segments, "captions": cap_out, "ev": ev}
json.dump(tl, open(OUT, "w"), ensure_ascii=False, indent=1)
json.dump([[n, CL[n][0], CL[n][1]] for n in SEQ], open(CLOUT, "w"))
print(f"total {TOTAL}s  end card {END_CARD}  overload {OVERLOAD}  turn {START['t1']}  services {SVC_START}..{OUTCOME}")
for n in SEQ:
    print(n, clips[n]["start"], clips[n]["dur"])
for s in sections:
    print(s["key"], s["name"], s["start"], s["end"])
