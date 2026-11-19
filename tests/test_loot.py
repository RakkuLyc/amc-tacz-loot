#!/usr/bin/env python3
"""Testes automáticos das tabelas de loot (sem servidor e sem dependências: só a biblioteca padrão do Python).

Rodar na raiz do projeto:  python3 -m unittest -v

O que é conferido:
- os arquivos em src/main/resources/data são exatamente o que o gerador produz agora (nada editado à mão, nada
  esquecido)
  e duas gerações seguidas são idênticas (determinismo);
- estrutura de toda tabela: pesos inteiros > 0, sinais do `quality` (Sorte) e soma zero nos pools com `empty`;
- condição `neoforge:mod_loaded` em toda tabela e loot modifier com item de mod opcional;
- loot modifiers listados, existentes e apontando só para as 36 tabelas do AMC;
- IDs internos (GunId, AmmoId, ...) existem nos catálogos; nenhum item vanilla fora da sucata e das exceções;
  nenhum vaso; as 36 tabelas do AMC sobrescritas;
- a chance de cada item no disco é a da configuração do gerador;
- risco de estourar um container de 9 espaços (dispenser/dropper recebem a tabela `barrel`) abaixo de 1 em 100.000.

Limite: os testes que comparam com a configuração importam o próprio gen_loot; numa refatoração do gerador a prova de
"nada mudou" é o hash dos arquivos gerados contra um baseline, não estes testes.
"""
import contextlib
import filecmp
import io
import json
import math
import os
import re
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import gen_loot as G  # noqa: E402

DATA = os.path.join(ROOT, "src/main/resources/data")
OPTIONAL_MODS = ("firstaid", "sophisticatedbackpacks", "flashlight")
# Pilha máxima dos itens que podem passar dela num sorteio (conferido nos jars: index/throwable/*.json da LesRaisins;
# First Aid stacksTo(16)). Usado só na conta de estouro de container.
THROWABLE_STACK = {"m67": 3, "rgn": 3, "c4": 1}
FIRSTAID_STACK = 16


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def all_tables():
    out = {}
    for dp, _, fs in os.walk(DATA):
        for f in fs:
            p = os.path.join(dp, f)
            if "/loot_table/" in p:
                out[os.path.relpath(p, DATA)] = load(p)
    return out


TABLES = all_tables()
AMC_IDS = {"%s:chests/%s/%s" % (G.AMC, th, ti) for th in G.RATES
           for ti in ("chest", "chest_hard", "barrel", "barrel_hard", "pot", "pot_hard")}


class Generated(unittest.TestCase):
    def test_disk_equals_generator_and_deterministic(self):
        """O que está no repositório = o que o gerador produz; duas gerações seguidas são iguais."""
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            for d in (a, b):
                with contextlib.redirect_stdout(io.StringIO()):
                    G.write(d)                      # write() roda check() e encerra com erro se algo estiver errado
            for d in (a, b):
                cmp = filecmp.dircmp(d, DATA)
                self.assertEqual(self._diff(cmp), [], "arquivos diferentes do repositório (rode gen_loot.py --write)")

    def _diff(self, cmp):
        out = cmp.left_only + cmp.right_only + cmp.diff_files + cmp.funny_files
        for name in cmp.common_files:
            if not filecmp.cmp(os.path.join(cmp.left, name), os.path.join(cmp.right, name), shallow=False):
                out.append(os.path.join(cmp.left, name))
        for sub in cmp.subdirs.values():
            out += self._diff(sub)
        return sorted(set(out))


class Structure(unittest.TestCase):
    def test_weights_and_luck_signs(self):
        for name, t in TABLES.items():
            self.assertEqual(t["type"], "minecraft:chest", name)
            for i, p in enumerate(t["pools"]):
                where = "%s pool %d" % (name, i)
                for e in p["entries"]:
                    w = e.get("weight", 1)
                    self.assertTrue(isinstance(w, int) and w > 0, "%s: peso inválido %r" % (where, w))
                    q = e.get("quality", 0)
                    if e["type"] == "minecraft:empty":
                        self.assertLessEqual(q, 0, where + ": empty com quality positivo")
                    else:
                        self.assertGreaterEqual(q, 0, where + ": item com quality negativo")
                if any(e["type"] == "minecraft:empty" for e in p["entries"]):
                    self.assertEqual(sum(e.get("quality", 0) for e in p["entries"]), 0,
                                     where + ": soma dos quality != 0")

    def test_optional_mods_have_condition(self):
        for name, t in TABLES.items():
            s = json.dumps(t)
            mods = {c.get("modid") for c in t.get("neoforge:conditions", [])}
            for m in OPTIONAL_MODS:
                if '"%s:' % m in s:
                    self.assertIn(m, mods, "%s: item de %s sem condição mod_loaded" % (name, m))

    def test_loot_modifiers(self):
        gl = load(os.path.join(DATA, "neoforge/loot_modifiers/global_loot_modifiers.json"))
        self.assertIs(gl["replace"], False)
        folder = os.path.join(DATA, G.MOD, "loot_modifiers")
        files = {f[:-5] for f in os.listdir(folder)}
        self.assertEqual(set(e.split(":")[1] for e in gl["entries"]), files, "lista != arquivos de loot modifier")
        for f in files:
            g = load(os.path.join(folder, f + ".json"))
            self.assertIn(g["conditions"][0]["loot_table_id"], AMC_IDS, f + ": alvo fora das tabelas do AMC")
            ns, path = g["table"].split(":")
            t = TABLES.get(os.path.join(ns, "loot_table", path + ".json"))
            self.assertIsNotNone(t, f + ": tabela inexistente")
            self.assertEqual({c["modid"] for c in g.get("neoforge:conditions", [])},
                             {c["modid"] for c in t.get("neoforge:conditions", [])}, f + ": condição != da tabela")

    def test_ids_exist_in_catalogs(self):
        lr = load(os.path.join(ROOT, "docs/lr_catalog.json"))
        known = {"GunId": G.TZ["guns"], "AmmoId": G.TZ["ammo"], "AttachmentId": G.TZ["attachments"], "ConsumableId": lr,
                 "ThrowableId": THROWABLE_STACK,
                 "MeleeWeaponId": {i for i, d in G.GEAR.items() if d["item"] == "melee"}}
        pattern = (r'(GunId|AmmoId|AttachmentId|ConsumableId|ThrowableId|MeleeWeaponId)'
                   r'\\?"?\s*:\s*\\?"[a-z]+:([a-z_0-9]+)')
        found = 0
        for name, t in TABLES.items():
            for kind, iid in re.findall(pattern, json.dumps(t)):
                found += 1
                self.assertIn(iid, known[kind], "%s: %s=%s fora do catálogo" % (name, kind, iid))
        self.assertGreater(found, 400, "a busca de IDs internos não encontrou quase nada: expressão quebrada?")

    def test_all_36_amc_tables_overridden(self):
        """As 36 tabelas do AMC (6 temas x 6 tiers, lista fixa aqui) existem como sucata.

        Sem uma delas o loot vanilla do AMC voltaria."""
        themes = ("building", "police_station", "pharmacy", "house", "workshop", "gas_station")
        tiers = ("chest", "chest_hard", "barrel", "barrel_hard", "pot", "pot_hard")
        want = {os.path.join(G.AMC, "loot_table/chests", th, ti + ".json") for th in themes for ti in tiers}
        got = {n for n in TABLES if n.startswith(os.path.join(G.AMC, "loot_table/chests") + os.sep)}
        self.assertEqual(got, want)

    def test_no_pot_tables_and_vanilla_only_junk(self):
        allowed = {"minecraft:" + i for i in list(G.JUNK) + list(G.TOOLS)} | {"minecraft:bread"}
        for name, t in TABLES.items():
            if name.startswith(G.MOD + "/"):
                self.assertNotRegex(name, r"/pot(_hard)?_", "tabela de vaso no namespace do mod")
            for item in re.findall(r'"name": "(minecraft:[a-z_0-9]+)"', json.dumps(t)):
                self.assertIn(item, allowed, "%s: item vanilla fora da sucata" % name)


class Chances(unittest.TestCase):
    def test_each_item_chance_equals_config(self):
        """Chance de cada sorteio no disco (Sorte 0) = configuração do gerador, em todos os temas e tiers."""
        for th in G.RATES:
            for ti in G.TIERS:
                want = {i: p / 1000 for _, i, p in G.item_chances(th, ti)}
                want.update({i: p / 1000 for i, p in G.fa_chances(th, ti)})
                for fam in G.LEVEL_FAMILIES:
                    want.update({i: p / 1000 for i, _, p in G.family_chances(fam, th, ti)})
                core = {c: v / 1000 for c, v in G.RATES[th][ti].items()}
                got, got_core = {}, {}
                for kind in ("core", "firstaid", "backpacks", "flashlight"):
                    t = TABLES.get(os.path.join(G.MOD, "loot_table", th, "%s_%s.json" % (ti, kind)))
                    for p in (t or {"pools": []})["pools"]:
                        tot = sum(e["weight"] for e in p["entries"])
                        for e in p["entries"]:
                            if e["type"] == "minecraft:loot_table":
                                got_core[e["value"].split("/")[-1].split("_")[0]] = e["weight"] / tot
                            elif e["type"] == "minecraft:item":
                                got[self._item_name(e)] = e["weight"] / tot
                where = "%s/%s" % (th, ti)
                self.assertEqual(set(got), set(want), where + ": itens no disco != configuração")
                self.assertEqual(set(got_core), set(core), where + ": categorias no disco != configuração")
                for k in want:
                    self.assertAlmostEqual(got[k], want[k], delta=max(0.5e-5, 0.005 * want[k]),
                                           msg="%s %s" % (where, k))
                for k in core:
                    self.assertAlmostEqual(got_core[k], core[k], places=9, msg="%s [%s]" % (where, k))

    @staticmethod
    def _item_name(e):
        s = json.dumps(e.get("functions", []))
        m = re.search(r'(?:ConsumableId|ThrowableId|MeleeWeaponId)\\?"?\s*:\s*\\?"[a-z]+:([a-z_0-9]+)', s)
        if m:
            return m.group(1)
        if e["name"] == "tacz:ammo_box":
            level = int(re.search(r"Level:(\d+)", s).group(1))
            return [k for k, d in G.AMMO_BOX.items() if d["level"] == level][0]
        return e["name"].split(":")[1]


class Overflow(unittest.TestCase):
    """Nº de pilhas por container (distribuição exata, Sorte 0).

    Soma core + First Aid + mochilas + lanternas + sucata do AMC."""
    LIMIT = 1e-5

    def test_nine_slot_containers(self):
        for th in G.RATES:
            for ti in ("barrel", "barrel_hard"):
                d = self._dist(TABLES[os.path.join(G.AMC, "loot_table/chests", th, ti + ".json")])
                for kind in ("core", "firstaid", "backpacks", "flashlight"):
                    t = TABLES.get(os.path.join(G.MOD, "loot_table", th, "%s_%s.json" % (ti, kind)))
                    if t:
                        d = self._conv(d, self._dist(t))
                self.assertLess(sum(d[10:]), self.LIMIT, "%s/%s: chance de mais de 9 pilhas" % (th, ti))

    @staticmethod
    def _conv(a, b):
        r = [0.0] * (len(a) + len(b) - 1)
        for i, x in enumerate(a):
            for j, y in enumerate(b):
                r[i + j] += x * y
        return r

    def _max_stack(self, e):
        if e["name"] == "lrtactical:throwable":
            return THROWABLE_STACK[re.search(r'"ThrowableId": "lrtactical:([a-z_0-9]+)"', json.dumps(e)).group(1)]
        if e["name"].startswith("firstaid:"):
            return FIRSTAID_STACK
        return 64        # munição sai sempre dentro da pilha do calibre; os demais itens têm pilha >= o máximo sorteado

    def _entry(self, e):
        if e["type"] == "minecraft:empty":
            return [1.0]
        if e["type"] == "minecraft:loot_table":
            ns, path = e["value"].split(":")
            return self._dist(TABLES[os.path.join(ns, "loot_table", path + ".json")])
        lo = hi = 1
        for f in e.get("functions", []):
            if f["function"] == "minecraft:set_count":
                c = f["count"]
                lo, hi = (c, c) if isinstance(c, int) else (int(c["min"]), int(c["max"]))
        d = [0.0] * 4
        for c in range(lo, hi + 1):
            d[math.ceil(c / self._max_stack(e))] += 1 / (hi - lo + 1)
        return d

    def _pool(self, p):
        tot = sum(e.get("weight", 1) for e in p["entries"])
        one = [0.0]
        for e in p["entries"]:
            d = self._entry(e)
            one += [0.0] * (len(d) - len(one))
            for i, x in enumerate(d):
                one[i] += e.get("weight", 1) / tot * x
        r = p["rolls"]
        rolls = {int(r): 1.0} if not isinstance(r, dict) else {k: 1 / (int(r["max"]) - int(r["min"]) + 1)
                                                                for k in range(int(r["min"]), int(r["max"]) + 1)}
        out = [0.0]
        for k, pk in rolls.items():
            d = [1.0]
            for _ in range(k):
                d = self._conv(d, one)
            out = [(out[i] if i < len(out) else 0) + pk * (d[i] if i < len(d) else 0)
                   for i in range(max(len(out), len(d)))]
        chance = 1.0
        for c in p.get("conditions", []):
            if c["condition"] == "minecraft:random_chance":
                chance *= c["chance"]
        return [(1 - chance) + chance * out[0]] + [chance * x for x in out[1:]]

    def _dist(self, t):
        d = [1.0]
        for p in t["pools"]:
            d = self._conv(d, self._pool(p))
        return d


if __name__ == "__main__":
    unittest.main()
