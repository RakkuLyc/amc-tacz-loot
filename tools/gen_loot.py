#!/usr/bin/env python3
"""Gerador das loot tables do AMC TACZ Loot.

  python3 -I tools/gen_loot.py            -> só imprime a PRÉVIA (esperados por estrutura, Sorte 0 a 3); não escreve nada
  python3 -I tools/gen_loot.py --write    -> apaga e reescreve src/main/resources/data/amctaczloot e o
                                             global_loot_modifiers.json (o gerador é dono desses arquivos)

Dados de entrada (gerados por tools/tacz_catalog.py, tools/lr_catalog.py, tools/measure_containers.py):
  docs/tacz_catalog.json  docs/lr_catalog.json  docs/containers.json

Como a Sorte entra (confirmado no bytecode do Minecraft 1.21.1):
  peso efetivo de uma entrada = floor(weight + quality * Sorte)   (nunca menos que 0)
  rolagens de um pool         = rolls + floor(bonus_rolls * Sorte)
Por isso: `quality` é a alavanca que responde já na Sorte I; `bonus_rolls` abaixo de 1 só age de Sorte II/III em diante.
Sucata: o mod também SOBRESCREVE as 42 tabelas do AMC (data/abandonedmoderncity/loot_table/chests/...) só com sucata,
para não restar item vanilla útil; o mod carrega DEPOIS do AMC (mods.toml, ordering AFTER).
Vasos (pot) ficam de fora dos prêmios: o Minecraft chama unpackLootTable(null) neles (sem Sorte) e, se a tabela gera mais itens
que espaços, o container fica VAZIO ("Tried to over-fill a container"); um vaso tem 1 espaço.
"""
import json, math, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "src/main/resources/data")
AMC = "abandonedmoderncity"
MOD = "amctaczloot"

# =====================================================================================================================
# NÚMEROS (tudo que se ajusta fica aqui). Probabilidades em ‰ (por mil) por rolagem de UM container, com Sorte 0.
# O resto (1000 - soma) é a entrada `empty`: o container ganha nada deste mod.
# =====================================================================================================================
LUCK_QUALITY = 0.25      # cada nível de Sorte multiplica a chance de cada categoria por (1 + 0.25 * Sorte)
# rolagens por tier: (rolls, bonus_rolls).  floor(bonus*Sorte): 0.34 soma 1 rolagem só na Sorte III; 0.2 só na Sorte V
ROLLS = {"chest": (1, 0.2), "chest_hard": (1, 0.34), "barrel": (1, 0.0), "barrel_hard": (1, 0.0)}
# chance (‰) por rolagem de cada categoria, por tema e tier.  gun = arma (sem munição junto), ammo = pilha de munição (pool próprio),
# att = attachment, fa = cura First Aid (tabela à parte, só se o First Aid estiver instalado).
# A cura LesRaisins, o leite condensado e o pão NÃO estão aqui: cada item tem a sua chance por container (HEAL_LR / FOOD abaixo).
RATES = {
    "building":       {"chest": dict(gun=120, ammo=520, att=40, fa=40),         # 1 arma a cada 8,3 baús; munição em 52%
                       "chest_hard": dict(gun=200, ammo=866, att=70, fa=70),     # 1 arma a cada 5 baús difíceis; munição 86,6%
                       "barrel": dict(gun=4, ammo=62, att=12, fa=15),
                       "barrel_hard": dict(gun=7, ammo=114, att=24, fa=30)},
    "police_station": {"chest": dict(gun=250, ammo=800, att=90, fa=50),          # armas inalteradas: 1 a cada 4 baús; munição 80%
                       "chest_hard": dict(gun=333, ammo=1000, att=160, fa=80),   # 1 arma a cada 3 baús difíceis; munição sempre (teto)
                       "barrel": dict(gun=30, ammo=200, att=40, fa=20),
                       "barrel_hard": dict(gun=60, ammo=360, att=70, fa=35)},
    "pharmacy":       {"chest": dict(fa=300), "chest_hard": dict(fa=400),
                       "barrel": dict(fa=120), "barrel_hard": dict(fa=200)},
    "house":          {"chest": dict(fa=30), "chest_hard": dict(fa=60),
                       "barrel": dict(fa=10), "barrel_hard": dict(fa=20)},
    "workshop":       {"chest": dict(ammo=40, fa=20), "chest_hard": dict(ammo=70, fa=40),
                       "barrel": dict(ammo=15, fa=8), "barrel_hard": dict(ammo=30, fa=15)},
    "gas_station":    {"chest": dict(fa=30), "chest_hard": dict(fa=60),
                       "barrel": dict(fa=10), "barrel_hard": dict(fa=20)},
}
# (o tema building_large foi removido do AMC em 14 Nov 2026, commit 72d07b3: todo prédio usa `building`)
# raridade das armas por tipo (peso relativo entre tipos) e perfis de tema
GUN_TYPE_W = {
    "default": dict(pistol=10, smg=6, shotgun=6, rifle=4, dmr=2, sniper=1.5, mg=1, rpg=0.3),
    "police":  dict(pistol=8, smg=8, shotgun=8, rifle=6, dmr=2.5, sniper=1.5, mg=1, rpg=0.3),
}
GUN_PROFILE = {"police_station": "police"}          # os demais temas usam "default"
# MUNIÇÃO (escolhas do usuário, 14-15 Nov 2026): a quantidade por pilha é proporcional à pilha máxima do calibre, tomando o
# 9mm como referência (24 a 50 balas). A chance de cada calibre é MISTA: AMMO_MIX_UNIFORM da chance é igual para todos os
# calibres que têm alguma arma e o resto acompanha a popularidade das armas que o usam (peso das armas do tema). Com 1.0 seria
# tudo igual; com 0.0, só pela popularidade. (Com poucas armas achadas, calibres todos iguais deixavam ~24% da munição útil.)
AMMO_REF = ("9mm", 24, 50)
AMMO_MIX_UNIFORM = 0.5
# (a arma NÃO traz munição junto: a munição é um sorteio separado, calibre pela raridade das armas que o usam)
ATT_TYPE_W = dict(scope=4, muzzle=4, grip=3, stock=3, extended_mag=4, laser=2)   # peso do tipo de attachment
# itens de cura: (peso, mín, máx)
# CURA LESRAISINS (escolha do usuário, 15 Nov 2026): chance de CADA item por container, independente dos outros (‰: 195 = 19,5%),
# a mesma em todos os temas e tipos de container, exceto na farmácia (multiplicador só nos incomuns e no raro, PHARMACY_MULT).
# Classes: Comuns = golden star, amoxicillin, ibuprofen, vaseline; Incomuns = CMS, AI-2, CAR, blood pack; Raro = SURV12.
# SURV12: 3% pedido pelo usuário, depois "diminuir levemente a raridade" (= um pouco mais comum): 4%.
HEAL_LR = dict(vaseline=195, ibuprofen=190, amoxycillin=180, goldenstar=170, blood_pack=90, carfak=85, ai2=80, cms=70, surv12=40)
HEAL_CLASS = dict(vaseline="Comum", ibuprofen="Comum", amoxycillin="Comum", goldenstar="Comum",
                  blood_pack="Incomum", carfak="Incomum", ai2="Incomum", cms="Incomum", surv12="Raro")
PHARMACY_MULT = {"Comum": 1.0, "Incomum": 2.0, "Raro": 2.0}
# Fator geral sobre as chances de cura LesRaisins acima (15 Nov 2026: "exagerei um pouco" -> opção C, tudo x0,5). Vale por cima do
# multiplicador da farmácia. Não mexe no leite, no pão nem no First Aid. Valores resultantes arredondados em ‰ (ex.: 19,5% -> 9,8%).
HEAL_SCALE = 0.5
# COMIDA: chance por container (‰) e quantidade; themes=None = todos os temas. O pão é vanilla (exceção explícita do usuário) e só em casas.
FOOD = dict(condensed_milk=dict(p=80, lo=2, hi=4, themes=None), bread=dict(p=200, lo=4, hi=12, themes=("house",)))
FA_W = dict(plaster=(12, 1, 3), bandage=(12, 1, 2), painkillers=(8, 1, 1), morphine=(4, 1, 1),
            morphine_injector=(3, 1, 1), adrenaline_injector=(2, 1, 1), defibrillator=(1, 1, 1))
# SUCATA: o mod sobrescreve as 42 tabelas do AMC (mesmos caminhos) para que NÃO reste nenhum item vanilla útil nos containers.
# Só entra aqui o que tem pouca ou nenhuma utilidade: nome -> (peso, mín, máx). A mesma lista em todos os temas.
JUNK = dict(stick=(12, 1, 6), wheat_seeds=(10, 1, 4), beetroot_seeds=(8, 1, 4), melon_seeds=(8, 1, 4),
            pumpkin_seeds=(8, 1, 4), rotten_flesh=(10, 1, 3), bone=(8, 1, 3), paper=(8, 1, 4), bowl=(6, 1, 2),
            glass_bottle=(6, 1, 2), spider_eye=(4, 1, 1))
# quanto de sucata por container: (chance de ter algo em ‰, mín, máx de pilhas). Sem efeito de Sorte (sucata não é prêmio).
# Os tiers _hard têm a mesma sucata: o prêmio dos difíceis vem do mod, não de mais sucata.
JUNK_SHAPE = {"chest": (1000, 2, 4), "chest_hard": (1000, 2, 4), "barrel": (300, 1, 2), "barrel_hard": (300, 1, 2),
              "pot": (300, 1, 1), "pot_hard": (300, 1, 1)}
# categorias da tabela principal (TACZ + LesRaisins, obrigatórios) e da tabela do First Aid (opcional)
CORE_POOLS = (("gun", "att"), ("ammo",))      # sorteios independentes por rolagem do baú (a cura e a comida têm um pool por item)
CORE_CATS = ("gun", "ammo", "att")
LUCKS = (0, 1, 2, 3)
# =====================================================================================================================

TIERS = ("chest", "chest_hard", "barrel", "barrel_hard")


def load(p):
    return json.load(open(os.path.join(ROOT, p), encoding="utf-8"))


TZ = load("docs/tacz_catalog.json")
LR = load("docs/lr_catalog.json")
CONT = load("docs/containers.json")


# ---------------------------------------------------------------- escolha dos itens
def eligible_guns():
    return {g: v for g, v in TZ["guns"].items() if v["craftable"]}


def gun_weights(profile):
    guns = eligible_guns(); tw = GUN_TYPE_W[profile]
    n = {}
    for v in guns.values(): n[v["type"]] = n.get(v["type"], 0) + 1
    return {g: max(1, round(tw[v["type"]] * 1000 / n[v["type"]])) for g, v in guns.items()}


def ammo_weights(profile="default"):
    """Peso de cada calibre (só os que têm arma elegível; 7.62x25 e 6.8x51 Fury não têm): AMMO_MIX_UNIFORM igual para todos +
    o resto proporcional ao peso das armas do perfil que usam o calibre. Pesos inteiros, somando ~1000."""
    pop = {}
    for gun, w in gun_weights(profile).items():
        c = TZ["guns"][gun]["ammo"].split(":")[1]; pop[c] = pop.get(c, 0) + w
    tot = sum(pop.values()); n = len(pop)
    return {c: max(1, round(1000 * (AMMO_MIX_UNIFORM / n + (1 - AMMO_MIX_UNIFORM) * pop[c] / tot))) for c in sorted(pop)}


def ammo_range(c):
    """Mín e máx de balas por pilha: proporcional à pilha máxima, com o 9mm de referência (AMMO_REF)."""
    ref, lo9, hi9 = AMMO_REF; base = TZ["ammo"][ref]["stack"]; st = TZ["ammo"][c]["stack"] or 30
    lo = max(1, round(lo9 * st / base)); return lo, max(lo, round(hi9 * st / base))


def att_weights():
    items = {a: v for a, v in TZ["attachments"].items() if v["craftable"]}
    n = {}
    for v in items.values(): n[v["type"]] = n.get(v["type"], 0) + 1
    return {a: max(1, round(ATT_TYPE_W[v["type"]] * 100 / n[v["type"]])) for a, v in items.items()}


# ---------------------------------------------------------------- JSON dos itens
def custom(**kw):
    return {"function": "minecraft:set_components", "components": {"minecraft:custom_data": kw}}


def count(lo, hi):
    return {"function": "minecraft:set_count", "count": lo if lo == hi else {"type": "minecraft:uniform", "min": lo, "max": hi}}


def e_gun(g):
    return {"type": "minecraft:item", "name": "tacz:modern_kinetic_gun", "functions": [custom(
        GunId="tacz:" + g, GunFireMode=TZ["guns"][g]["fire_mode"][0], GunCurrentAmmoCount=0, HasBulletInBarrel=False)]}


def e_ammo(c):
    lo, hi = ammo_range(c)
    return {"type": "minecraft:item", "name": "tacz:ammo", "functions": [custom(AmmoId="tacz:" + c), count(lo, hi)]}


def e_att(a):
    return {"type": "minecraft:item", "name": "tacz:attachment", "functions": [custom(AttachmentId="tacz:" + a)]}


def e_lr(i, lo, hi):
    return {"type": "minecraft:item", "name": "lrtactical:consumable",
            "functions": [custom(ConsumableId="lrtactical:" + i)] + ([count(lo, hi)] if hi > 1 else [])}


def e_fa(i, lo, hi):
    return {"type": "minecraft:item", "name": "firstaid:" + i, "functions": [count(lo, hi)] if hi > 1 else []}


def table(pools, cond=None):
    t = {"type": "minecraft:chest", "pools": pools}
    if cond: t = {"neoforge:conditions": cond, **t}
    return t


def pool(entries, rolls=1, bonus=None):
    p = {"rolls": rolls, "entries": entries}
    if bonus is not None: p["bonus_rolls"] = bonus
    return p


def with_w(e, w):
    return {**e, "weight": w}


def pick_tables():
    """Tabelas de escolha (o que sai quando a categoria é sorteada). Nome -> (JSON, condição ou None)."""
    out = {}
    for prof in ("default", "police"):
        gw = gun_weights(prof)
        out["pick/gun_" + prof] = (table([pool([with_w(e_gun(g), w) for g, w in gw.items()])]), None)
        out["pick/ammo_" + prof] = (table([pool([with_w(e_ammo(c), w) for c, w in ammo_weights(prof).items()])]), None)
    out["pick/att"] = (table([pool([with_w(e_att(a), w) for a, w in att_weights().items()])]), None)
    out["pick/fa"] = (table([pool([with_w(e_fa(i, lo, hi), w) for i, (w, lo, hi) in FA_W.items()])],
                            [{"type": "neoforge:mod_loaded", "modid": "firstaid"}]), None)
    return out


def junk_tables():
    """Tabelas do AMC sobrescritas, só com sucata. Nome 'tema/tier' -> JSON (namespace abandonedmoderncity)."""
    ents = []
    for i, (w, lo, hi) in JUNK.items():
        e = {"type": "minecraft:item", "name": "minecraft:" + i, "weight": w}
        if hi > 1: e["functions"] = [count(lo, hi)]
        ents.append(e)
    out = {}
    for theme in RATES:
        for tier, (chance, lo, hi) in JUNK_SHAPE.items():
            p = {"rolls": lo if lo == hi else {"type": "minecraft:uniform", "min": lo, "max": hi}, "bonus_rolls": 0.0, "entries": ents}
            if chance < 1000: p["conditions"] = [{"condition": "minecraft:random_chance", "chance": chance / 1000}]
            out["%s/%s" % (theme, tier)] = table([p])
    return out


def item_chances(theme):
    """Itens com chance própria neste tema: lista de (tipo, item, p em ‰). Farmácia: multiplicador nos incomuns e no raro."""
    out = []
    for i, p in HEAL_LR.items():
        m = PHARMACY_MULT[HEAL_CLASS[i]] if theme == "pharmacy" else 1.0
        out.append(("lr", i, max(1, min(1000, int(p * m * HEAL_SCALE + 0.5)))))
    for i, f in FOOD.items():
        if f["themes"] is None or theme in f["themes"]: out.append(("food", i, f["p"]))
    return out


def e_item(kind, i):
    if i == "bread": return {"type": "minecraft:item", "name": "minecraft:bread", "functions": [count(FOOD["bread"]["lo"], FOOD["bread"]["hi"])]}
    if i == "condensed_milk": return e_lr(i, FOOD[i]["lo"], FOOD[i]["hi"])
    return e_lr(i, 1, 1)


def item_pool(kind, i, p, rolls=1, bonus=0.0):
    """Um sorteio independente: o item com chance p (‰) ou nada. A Sorte sobe a chance pelo `quality`, como nas outras categorias."""
    q = max(1, round(p * LUCK_QUALITY))
    ents = [{**e_item(kind, i), "weight": p, "quality": q}]
    if p < 1000: ents.append({"type": "minecraft:empty", "weight": 1000 - p, "quality": -q})
    return pool(ents, rolls, bonus)


def weights(rates):
    """(weight, quality) por categoria + empty, somando 1000 em Sorte 0 e mantendo ~1000 com Sorte (quality do empty
    é o negativo da soma das outras)."""
    res = {}
    for c, w in rates.items(): res[c] = (w, max(1, round(w * LUCK_QUALITY)))
    res["empty"] = (1000 - sum(w for w, _ in res.values()), -sum(q for _, q in res.values()))
    return res


def main_tables():
    """Para cada tema/tier: tabela principal (core) e tabela do First Aid. Nome -> JSON."""
    out = {}
    for theme, tiers in RATES.items():
        prof = GUN_PROFILE.get(theme, "default")
        for tier, rates in tiers.items():
            rolls, bonus = ROLLS[tier]
            pools = []
            for group in CORE_POOLS:
                part = {k: v for k, v in rates.items() if k in group}
                if not part: continue
                ent = []
                for c, (w, q) in weights(part).items():
                    if c == "empty" and w <= 0: continue          # chance 100%: sem entrada vazia (peso 0 não vale)
                    if c == "empty": e = {"type": "minecraft:empty"}
                    else: e = {"type": "minecraft:loot_table", "value": "%s:pick/%s" % (MOD, {"gun": "gun_" + prof, "ammo": "ammo_" + prof, "att": "att", "lr": "lr"}[c])}
                    ent.append({**e, "weight": w, "quality": q})
                pools.append(pool(ent, rolls, bonus))
            for kind, i, p in item_chances(theme): pools.append(item_pool(kind, i, p))
            out["%s/%s_core" % (theme, tier)] = table(pools)
            if "fa" in rates:
                ent = []
                for c, (w, q) in weights({"fa": rates["fa"]}).items():
                    e = {"type": "minecraft:empty"} if c == "empty" else {"type": "minecraft:loot_table", "value": MOD + ":pick/fa"}
                    ent.append({**e, "weight": w, "quality": q})
                out["%s/%s_firstaid" % (theme, tier)] = table([pool(ent, rolls, bonus)], [{"type": "neoforge:mod_loaded", "modid": "firstaid"}])
    return out


# ---------------------------------------------------------------- esperados (a mesma conta do Minecraft)
def eff(w, q, luck):
    return max(0, math.floor(w + q * luck))


def expected(theme, tier, luck):
    """Esperado por container (stacks): guns, ammo, att, lr, fa."""
    rates = RATES[theme][tier]; rolls, bonus = ROLLS[tier]
    r = rolls + math.floor(bonus * luck)
    res = {k: 0.0 for k in ("gun", "ammo", "att", "lr", "fa", "food")}
    for cat_set in (*CORE_POOLS, ("fa",)):
        part = {k: v for k, v in rates.items() if k in cat_set}
        if not part: continue
        wq = weights(part)
        tot = sum(eff(w, q, luck) for w, q in wq.values())
        for c in part:
            p = eff(*wq[c], luck) / tot if tot else 0
            avg = {"fa": sum(w * (lo + hi) / 2 for w, lo, hi in FA_W.values()) / sum(w for w, _, _ in FA_W.values())}.get(c, 1)
            res[c] += r * p * avg
    for kind, i, p0 in item_chances(theme):           # um sorteio por item (rolagem única, sem bonus)
        q = max(1, round(p0 * LUCK_QUALITY)); a = eff(p0, q, luck); e0 = eff(1000 - p0, -q, luck)
        res[kind] += a / (a + e0) if a + e0 else 0
    return res


def preview():
    # estruturas por tema
    rows = []
    for name, v in CONT.items():
        th = v["theme"]
        if th not in RATES: continue
        rows.append((th, name, v))
    rows.sort(key=lambda r: (list(RATES).index(r[0]), -r[2]["total"]))
    print("Esperado por estrutura (uma instância): armas | pilhas de munição | attachments | cura LesRaisins | cura First Aid")
    print("Sorte 0 detalhada; 'armas' também em Sorte 1/2/3. Vasos não recebem nada do mod.\n")
    print("%-14s %-30s %5s | %s | %-23s | %6s %6s" % ("tema", "estrutura", "cont.", "Sorte 0: arm  mun  att   LR   FA", "armas S0 S1 S2 S3", "LR S3", "FA S3"))
    for th, name, v in rows:
        def tot(luck):
            t = {k: 0.0 for k in ("gun", "ammo", "att", "lr", "fa", "food")}
            for tier, n in v["tiers"].items():
                if tier.startswith("pot"): continue
                for k, x in expected(th, tier, luck).items(): t[k] += n * x
            return t
        e = [tot(l) for l in LUCKS]
        print("%-14s %-30s %5d | %17.1f %4.1f %4.1f %4.1f %4.1f | %5.1f %4.1f %4.1f %4.1f | %5.1f %5.1f" % (
            th, name, v["total"], e[0]["gun"], e[0]["ammo"], e[0]["att"], e[0]["lr"], e[0]["fa"],
            e[0]["gun"], e[1]["gun"], e[2]["gun"], e[3]["gun"], e[3]["lr"], e[3]["fa"]))
    print("\nBaús (chest + chest_hard) por arma, Sorte 0 / I / II / III  (1 arma a cada N baús):")
    for th in ("building", "police_station"):
        cells = []
        for l in LUCKS:
            n = sum(c for _, nm, v in rows if nm == "abandoned_police_station" and th == "police_station" for tr, c in v["tiers"].items() if tr.startswith("chest")) or 1
            ex = 0.0; ch = 0
            for _, nm, v in rows:
                if v["theme"] != th: continue
                for tr, c in v["tiers"].items():
                    if tr.startswith("chest"): ex += c * expected(th, tr, l)["gun"]; ch += c
            cells.append("S%d: 1 a cada %.1f" % (l, ch / ex))
        print("  %-15s %s" % (th, "   ".join(cells)))
    gun_p = []
    for tr, c in CONT["abandoned_police_station"]["tiers"].items():
        if tr.startswith("pot"): continue
        r_, b_ = ROLLS[tr]; q = expected("police_station", tr, 0)["gun"]; gun_p += [q] * c
    dist = [1.0]
    for q in gun_p:
        dist = [(dist[k] if k < len(dist) else 0) * (1 - q) + (dist[k - 1] * q if k > 0 else 0) for k in range(len(dist) + 1)]
    print("Delegacia, Sorte 0: chance de ter pelo menos N armas: " + "  ".join("N=%d: %.0f%%" % (n, 100 * sum(dist[n:])) for n in (3, 4, 5, 6, 7, 8)))
    print("\nChance de UM baú (chest) ter pelo menos 1 item do mod (TACZ+LesRaisins | + First Aid), por tema e Sorte:")
    for th in RATES:
        for tier in ("chest", "chest_hard"):
            cells = []
            for l in LUCKS:
                rolls, bonus = ROLLS[tier]; r = rolls + math.floor(bonus * l)
                p_none = 1.0
                for group in CORE_POOLS:
                    part = {k: v for k, v in RATES[th][tier].items() if k in group}
                    if not part: continue
                    wq = weights(part); tot = sum(eff(w, q, l) for w, q in wq.values())
                    p_none *= (eff(*wq["empty"], l) / tot) ** r
                for kind, i, p0 in item_chances(th):
                    q0 = max(1, round(p0 * LUCK_QUALITY)); a0 = eff(p0, q0, l); e0 = eff(1000 - p0, -q0, l)
                    p_none *= (e0 / (a0 + e0)) if a0 + e0 else 1.0
                p_core = 1 - p_none
                fa = weights({"fa": RATES[th][tier]["fa"]}); tf = sum(eff(w, q, l) for w, q in fa.values())
                p_fa = 1 - (eff(*fa["empty"], l) / tf) ** r
                cells.append("S%d %4.0f%%|%4.0f%%" % (l, 100 * p_core, 100 * (1 - (1 - p_core) * (1 - p_fa))))
            print("  %-14s %-11s %s" % (th, tier, "   ".join(cells)))


# ---------------------------------------------------------------- escrita + verificações
def write():
    base = os.path.join(OUT, MOD)
    amc_dir = os.path.join(OUT, AMC)
    for d in (base, amc_dir):
        if os.path.isdir(d): shutil.rmtree(d)
    gl = os.path.join(OUT, "neoforge/loot_modifiers/global_loot_modifiers.json")
    def w(path, obj):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w", encoding="utf-8").write(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")
    tables, glms = {}, {}
    for n, (t, _) in pick_tables().items(): tables[n] = t
    for n, t in main_tables().items(): tables[n] = t
    for n, t in tables.items(): w("%s/loot_table/%s.json" % (base, n), t)
    junk = junk_tables()
    for n, t in junk.items(): w("%s/loot_table/chests/%s.json" % (amc_dir, n), t)
    for n in main_tables():
        theme, rest = n.split("/"); tier, kind = rest.rsplit("_", 1)
        g = {"type": "neoforge:add_table",
             "conditions": [{"condition": "neoforge:loot_table_id", "loot_table_id": "%s:chests/%s/%s" % (AMC, theme, tier)}],
             "table": "%s:%s" % (MOD, n)}
        if kind == "firstaid": g["neoforge:conditions"] = [{"type": "neoforge:mod_loaded", "modid": "firstaid"}]
        glms["%s_%s_%s" % (kind, theme, tier)] = g
    for n, g in glms.items(): w("%s/loot_modifiers/%s.json" % (base, n), g)
    w(gl, {"replace": False, "entries": ["%s:%s" % (MOD, n) for n in glms]})
    check(base, gl, tables, glms, junk)
    print("escrito: %d tabelas, %d loot modifiers, %d tabelas do AMC sobrescritas (só sucata)" % (len(tables), len(glms), len(junk)))


def check(base, gl, tables, glms, junk):
    """Verificações de consistência dos arquivos gerados; encerra com erro se algo estiver errado."""
    errs = []
    listed = json.load(open(gl))["entries"]
    for e in listed:
        if not os.path.exists("%s/loot_modifiers/%s.json" % (base, e.split(":")[1])): errs.append("GLM listado não existe: " + e)
    for n in glms:
        if "%s:%s" % (MOD, n) not in listed: errs.append("GLM existe mas não está listado: " + n)
    amc_ids = {"%s:chests/%s/%s" % (AMC, th, ti) for th in RATES for ti in TIERS}
    for n, g in glms.items():
        if g["table"].split(":")[1] not in tables: errs.append("GLM aponta para tabela inexistente: " + n)
        if g["conditions"][0]["loot_table_id"] not in amc_ids: errs.append("alvo não é tabela do AMC: " + n)
    for n, t in tables.items():
        s = json.dumps(t)
        if "firstaid:" in s and t.get("neoforge:conditions") != [{"type": "neoforge:mod_loaded", "modid": "firstaid"}]:
            errs.append("item do First Aid em tabela sem condição mod_loaded: " + n)
        if "pot" in n: errs.append("tabela de vaso gerada: " + n)
        for ref in [x for x in s.split('"') if x.startswith(MOD + ":pick/")]:
            if ref.split(":")[1] not in tables: errs.append("tabela de escolha inexistente: " + ref)
    # nenhum item vanilla fora da lista de sucata, em NENHUMA tabela gerada (mod + sobrescritas do AMC)
    allowed = {"minecraft:" + i for i in JUNK} | {"minecraft:bread"}
    for n, t in list(tables.items()) + [("amc:" + k, v) for k, v in junk.items()]:
        for name in re.findall(r'"name": "(minecraft:[a-z_0-9]+)"', json.dumps(t)):
            if name not in allowed: errs.append("item vanilla fora da sucata em %s: %s" % (n, name))
    expect = {"%s/%s" % (th, ti) for th in RATES for ti in ("chest", "chest_hard", "barrel", "barrel_hard", "pot", "pot_hard")}
    if set(junk) != expect: errs.append("tabelas do AMC sobrescritas != as 42 do AMC")
    for g, v in TZ["guns"].items():
        if v["ammo"].split(":")[1] not in TZ["ammo"]: errs.append("munição da arma %s fora do catálogo" % g)
    if errs:
        print("\n".join("ERRO: " + e for e in errs)); sys.exit(1)


if __name__ == "__main__":
    preview()
    if "--write" in sys.argv: write()
