#!/usr/bin/env python3
"""Extrai do jar do TACZ o catálogo de armas, munições e attachments -> docs/tacz_catalog.json.
Uso: python3 -I tools/tacz_catalog.py <tacz.jar>"""
import json, re, sys, zipfile, collections
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jsonc import jsonc

def main(jar):
    z = zipfile.ZipFile(jar); names = set(z.namelist())
    base = "assets/tacz/custom/tacz_default_gun/data/tacz/"
    load = lambda n: jsonc(z.read(n).decode("utf-8-sig"))
    ids = lambda k: sorted(n[len(base + "index/" + k + "/"):-5] for n in names
                           if n.startswith(base + "index/" + k + "/") and n.endswith(".json"))
    cat = {"guns": {}, "ammo": {}, "attachments": {}}
    for g in ids("guns"):
        ix = load(base + "index/guns/%s.json" % g); d = load(base + "data/guns/%s_data.json" % g)
        cat["guns"][g] = {"type": ix["type"], "ammo": d["ammo"], "mag": d.get("ammo_amount"),
                          "fire_mode": [m.upper() for m in d["fire_mode"]]}
    for a in ids("ammo"): cat["ammo"][a] = {"stack": load(base + "index/ammo/%s.json" % a).get("stack_size")}
    for t in ids("attachments"): cat["attachments"][t] = {"type": load(base + "index/attachments/%s.json" % t)["type"]}
    # fabricáveis na mesa de armeiro (receita no pacote padrão): critério de "item normal", em vez de adivinhar pelo nome
    made = set()
    for n in names:
        if "/data/tacz/recipe/" in n and n.endswith(".json"):
            try:
                r = load(n)
            except Exception:
                continue
            res = r.get("result") or {}
            if res.get("id"): made.add((res.get("type"), res["id"]))
    for k, kind in (("guns", "gun"), ("ammo", "ammo"), ("attachments", "attachment")):
        for i, v in cat[k].items(): v["craftable"] = (kind, "tacz:" + i) in made
    json.dump(cat, open("docs/tacz_catalog.json", "w"), indent=1)
    g = cat["guns"]
    for k in cat: print(k, "fabricáveis:", sum(v["craftable"] for v in cat[k].values()), "de", len(cat[k]))
    print("armas", len(g), "| sem munição:", [k for k, v in g.items() if not v["ammo"]])
    print("modos de tiro:", dict(collections.Counter(m for v in g.values() for m in v["fire_mode"])))
    print("ak47/m4a1/qr_24/urgi:", {k: (g[k]["ammo"], g[k]["fire_mode"]) for k in ("ak47", "m4a1", "qr_24", "urgi")})

main(sys.argv[1])
