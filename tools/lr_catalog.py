#!/usr/bin/env python3
"""Extrai do jar da LesRaisins os itens consumíveis (-> docs/lr_catalog.json): cura, fome, pilha, durabilidade.
Uso: python3 -I tools/lr_catalog.py <lesraisins.jar>"""
import json, sys, zipfile
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jsonc import jsonc

z = zipfile.ZipFile(sys.argv[1]); out = {}
for n in sorted(z.namelist()):
    if n.startswith("data/lrtactical/index/consumable/") and n.endswith(".json"):
        d = jsonc(z.read(n).decode("utf-8-sig")); k = n.rsplit("/", 1)[1][:-5]; x = d.get("data", {})
        out[k] = {k2: x.get(k2) for k2 in ("heal", "food", "stack_size", "max_durability", "use_duration", "cooldown_category")}
        out[k]["effects"] = [e.get("effect") if isinstance(e, dict) else e for e in (x.get("effects") or x.get("effect") or [])] if isinstance(x.get("effects") or x.get("effect"), list) else None
json.dump(out, open("docs/lr_catalog.json", "w"), indent=1)
for k, v in out.items(): print("%-16s %s" % (k, v))
