#!/usr/bin/env python3
"""Classifica os attachments do TACZ em Comum/Incomum/Raro/Épico (-> docs/attachments_rarity.json e .csv) por DOIS fatores, 50% cada, comparados dentro de cada
tipo: (1) quantas armas (peso real do loot) aceitam o attachment (compatibilidade resolvida pelas tags allow_attachments) e (2) seus atributos (zoom, recuo,
precisão, nível do pente, dano/perfuração das munições, silenciador...). Raro = muito poder e poucas armas aceitam. Corte global: 40% Comum, 30% Incomum, 20% Raro,
10% Épico. Uso: python3 -I tools/att_rarity.py <tacz.jar>"""
import os, zipfile, sys, json, math, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jsonc import jsonc; import gen_loot as g
z = zipfile.ZipFile(sys.argv[1]); names = z.namelist()
B = "assets/tacz/custom/tacz_default_gun/"; D = B + "data/tacz/"
J = lambda p: jsonc(z.read(p).decode("utf-8-sig"))
tags = {n[len(D + "tacz_tags/attachments/"):-5]: J(n) for n in names if n.startswith(D + "tacz_tags/attachments/") and n.endswith(".json") and "allow_attachments/" not in n}
def expand(x, seen=()):
    out = set()
    for e in x:
        if e.startswith("#tacz:"):
            k = e[6:]
            if k in tags and k not in seen: out |= expand(tags[k], seen + (k,))
        else: out.add(e[5:] if e.startswith("tacz:") else e)
    return out
allow = {n.rsplit("/", 1)[1][:-5]: expand(J(n)) for n in names if n.startswith(D + "tacz_tags/attachments/allow_attachments/") and n.endswith(".json")}
cat = g.TZ; guns = list(cat["guns"]); GW = g.gun_weights("default"); TW = sum(GW.values())
elig = [a for a, v in cat["attachments"].items() if v["craftable"]]
def pop(a): return sum(GW[x] for x in guns if a in allow.get(x, set())) / TW          # chance de uma arma sorteada aceitar o attachment
def nacc(a): return sum(1 for x in guns if a in allow.get(x, set()))
def types_of(a): return collections.Counter(cat["guns"][x]["type"] for x in guns if a in allow.get(x, set()))
def mult(d, *path):
    for k in path:
        if not isinstance(d, dict) or k not in d: return None
        d = d[k]
    return d
def gain(m):          # multiplicador < 1 = melhora (recuo, imprecisão): ganho = 1 - m
    return 0.0 if m is None else (1 - m)
MISSING = []
def power(a):
    f = D + "data/attachments/%s_data.json" % a
    if f not in names: MISSING.append(a)
    d = J(f) if f in names else {}; p = 0.0; why = []
    disp = B + "assets/tacz/display/attachments/%s_display.json" % a
    if disp in names:
        zm = J(disp).get("zoom")
        if zm: z_ = max(zm); p += 1.0 * math.log2(max(z_, 1.0)) + (0.3 if z_ > 1 else 0); why.append("zoom %.1f" % z_)
    rec = d.get("recoil")
    if isinstance(rec, dict):
        r = (gain(mult(rec, "pitch", "multiplier")) + gain(mult(rec, "yaw", "multiplier"))) / 2
        p += 4 * r; why.append("recuo %+d%%" % round(-100 * r))
    acc = [gain(mult(d, k, "multiplier")) for k in ("aim_inaccuracy", "inaccuracy", "sneak_inaccuracy", "lie_inaccuracy") if k in d]
    if acc: p += 3 * (sum(acc) / len(acc)); why.append("precisão %+d%%" % round(-100 * sum(acc) / len(acc)))
    if "extended_mag_level" in d: p += 1.2 * d["extended_mag_level"]; why.append("pente nív.%d" % d["extended_mag_level"])
    for k, w in (("damage", 1.5), ("armor_ignore", 1.2), ("pierce", 0.8), ("head_shot", 0.6), ("ammo_speed", 0.5), ("explosion", 2.0), ("ignite", 1.0), ("effective_range", 0.8), ("rpm", 0.4), ("knockback", 0.3)):
        if k in d: p += w; why.append(k)
    if "silence" in d: p += 1.2; why.append("silencioso")
    if "flash_hider" in d: p += 0.5
    if "melee" in d: p += 0.5; why.append("corpo a corpo")
    return p, ", ".join(why)
rows = []
for a in elig:
    pw, why = power(a); rows.append(dict(id=a, type=cat["attachments"][a]["type"], n=nacc(a), pop=pop(a), power=pw, why=why))
def pct(vals):                                    # posição percentual (0..1) dentro do grupo
    s = sorted(vals); return {v: (s.index(v) + s.count(v) / 2) / len(s) for v in vals}
for ty in set(r["type"] for r in rows):
    grp = [r for r in rows if r["type"] == ty]; pp = pct([r["power"] for r in grp]); pq = pct([r["pop"] for r in grp])
    for r in grp: r["score"] = 0.5 * pp[r["power"]] + 0.5 * (1 - pq[r["pop"]])      # alto = mais raro (muito poder e poucas armas aceitam)
ranked = sorted(rows, key=lambda r: r["score"]); N = len(rows)
for i, r in enumerate(ranked): r["cls"] = "Comum" if i < 0.40 * N else "Incomum" if i < 0.70 * N else "Raro" if i < 0.90 * N else "Épico"
json.dump([dict(id=r["id"], type=r["type"], cls=r["cls"], guns_accept=r["n"], pop=round(r["pop"], 4), power=round(r["power"], 2), score=round(r["score"], 3), why=r["why"]) for r in sorted(rows, key=lambda r: r["id"])],
          open("docs/attachments_rarity.json", "w"), indent=1, ensure_ascii=False)
print("N =", N, "| classes:", dict(collections.Counter(r["cls"] for r in rows)))
print("por tipo x classe:"); tc = collections.defaultdict(collections.Counter)
for r in rows: tc[r["type"]][r["cls"]] += 1
for ty, c in tc.items(): print("  %-13s %s" % (ty, dict(c)))
print("armas sem lista de attachments:", [x for x in guns if x not in allow])
print("attachments sem arquivo de dados (só zoom contado):", MISSING)
