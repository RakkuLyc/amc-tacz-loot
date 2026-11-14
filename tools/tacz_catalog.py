#!/usr/bin/env python3
"""Extrai do jar do TACZ o catálogo de armas, munições e attachments -> docs/tacz_catalog.json.
Uso: python3 -I tools/tacz_catalog.py <tacz.jar>"""
import json, re, sys, zipfile, collections

def jsonc(text):
    """JSON tolerante, como o do TACZ: comentários // e /* */ e vírgula sobrando (respeita strings)."""
    out, i, n, instr = [], 0, len(text), False
    while i < n:
        c = text[i]
        if instr:
            out.append(c)
            if c == "\\":
                out.append(text[i + 1]); i += 1
            elif c == '"':
                instr = False
        elif c == '"':
            instr = True; out.append(c)
        elif text.startswith("//", i):
            while i < n and text[i] != "\n": i += 1
            continue
        elif text.startswith("/*", i):
            i = text.index("*/", i) + 2
            continue
        else:
            out.append(c)
        i += 1
    return json.loads(re.sub(r",(\s*[}\]])", r"\1", "".join(out)))

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
    json.dump(cat, open("docs/tacz_catalog.json", "w"), indent=1)
    g = cat["guns"]
    print("armas", len(g), "| sem munição:", [k for k, v in g.items() if not v["ammo"]])
    print("modos de tiro:", dict(collections.Counter(m for v in g.values() for m in v["fire_mode"])))
    print("ak47/m4a1/qr_24/urgi:", {k: (g[k]["ammo"], g[k]["fire_mode"]) for k in ("ak47", "m4a1", "qr_24", "urgi")})

main(sys.argv[1])
