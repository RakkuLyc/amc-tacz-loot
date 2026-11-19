#!/usr/bin/env python3
"""Gerador das loot tables do AMC TACZ Loot.

  python3 -I tools/gen_loot.py            -> só imprime a PRÉVIA (esperados por estrutura, Sorte 0 a 3); não grava nada
  python3 -I tools/gen_loot.py --write    -> apaga e reescreve src/main/resources/data/amctaczloot,
                                             src/main/resources/data/abandonedmoderncity e o global_loot_modifiers.json
                                             (o gerador é dono desses arquivos)

Dados de entrada (em docs/):
  tacz_catalog.json        armas, munições e attachments do TACZ (tools/tacz_catalog.py)
  ammo_rarity.json         nível de cada calibre (tools/att_from_nbt.py, estruturas .nbt do usuário)
  attachments_rarity.json  nível de cada attachment (tools/att_from_nbt.py)
  containers.json          containers por estrutura do AMC, só para a PRÉVIA (tools/measure_containers.py)
  (docs/lr_catalog.json, de tools/lr_catalog.py, é só referência: o gerador não o lê)

Como a Sorte entra (confirmado no bytecode do Minecraft 1.21.1):
  peso efetivo de uma entrada = floor(weight + quality * Sorte)   (nunca menos que 0)
  rolagens de um pool         = rolls + floor(bonus_rolls * Sorte)
Por isso: `quality` é a alavanca que responde já na Sorte I; `bonus_rolls` abaixo de 1 só age de Sorte II/III em diante.
Sucata: o mod também SOBRESCREVE as 36 tabelas do AMC (6 temas x chest/barrel/pot x normal/_hard)
(data/abandonedmoderncity/loot_table/chests/...) só com sucata, para não restar item vanilla útil; o mod carrega DEPOIS
do AMC (mods.toml, ordering AFTER).
Vasos (pot) ficam de fora dos prêmios: o Minecraft chama unpackLootTable(null) neles (sem Sorte) e, se a tabela gera
mais itens que espaços, preenche até acabar o espaço e PERDE o resto, escolhido ao acaso (LootTable.fill: "Tried to
over-fill a container"); um vaso tem 1 espaço, então o item do mod competiria com o do AMC.
"""
import json, math, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "src/main/resources/data")
AMC = "abandonedmoderncity"
MOD = "amctaczloot"

# =====================================================================================================================
# NÚMEROS (tudo que se ajusta fica aqui, até a linha de "=" do fim do bloco).
#
# Dois jeitos de escrever uma chance, conforme o usuário deu os números (os dois continuam valendo):
#   - em ‰ (por mil) por container, com Sorte 0: 92 = 9,2%    -> RATES, HEAL_LR, FA_CHANCE, FOOD, GEAR, TOOLS
#   - "1 a cada N" baús: 14 = 1/14 = 7,1%                     -> GUN_CAT_ONE_IN, AMMO_BOX, LEVEL_FAMILIES
# Nas categorias de RATES o resto (1000 - soma) é a entrada `empty`: o container não ganha nada daquela categoria.
# =====================================================================================================================
PER_MILLE = 1000          # escala das chances em ‰
LUCK_QUALITY = 0.25       # cada nível de Sorte multiplica a chance de cada categoria por (1 + 0.25 * Sorte)
TIERS = ("chest", "chest_hard", "barrel", "barrel_hard")
LUCKS = (0, 1, 2, 3)      # níveis de Sorte mostrados na prévia
# rolagens por tier: (rolls, bonus_rolls).  floor(bonus*Sorte): 0.34 soma 1 rolagem só na Sorte III; 0.2 só na Sorte V
ROLLS = {"chest": (1, 0.2), "chest_hard": (1, 0.34), "barrel": (1, 0.0), "barrel_hard": (1, 0.0)}

# chance (‰) por rolagem de cada categoria, por tema e tier.  gun = arma (sem munição junto),
# ammo = munição (pool próprio, 1 a 3 pilhas), att = attachment (calculado abaixo a partir de gun: ATT_FRACTION_OF_GUN).
# A cura LesRaisins, o First Aid, a comida, o equipamento etc. NÃO estão aqui: cada item tem a sua chance por container.
RATES = {
    # PRÉDIO (17 Nov 2026, "Opção A, manter 16,8%"): a soma das categorias do usuário (GUN_CAT_ONE_IN) dá 16,84% de arma
    # por baú (antes 12%); os demais tiers sobem pelo mesmo fator (16,84/12 = 1,404).
    # Attachments = ATT_FRACTION_OF_GUN (1,2) x arma: 202 / 337 / 7 / 12 ‰.
    "building":       {"chest": dict(gun=168, ammo=520),          # 1 arma a cada 5,95 baús; munição em 52%
                       "chest_hard": dict(gun=281, ammo=866),    # 1 arma a cada 3,6 baús difíceis; munição 86,6%
                       "barrel": dict(gun=6, ammo=62),
                       "barrel_hard": dict(gun=10, ammo=114)},
    # DELEGACIA (17 Nov 2026): a chance de TODAS as armas é 2x a do prédio (mesma divisão por categoria e nível; baú
    # 33,6%, difícil 56,2%, barris 1,2% / 2,0%). Attachments = 1,2 x arma (= 2x os do prédio: 403 / 674 / 14 / 24 ‰).
    # Munição = a MESMA chance do prédio (17 Nov 2026: 52 / 86,6 / 6,2 / 11,4%).
    "police_station": {"chest": dict(gun=336, ammo=520),          # 1 arma a cada 3 baús; munição como no prédio (52%)
                       "chest_hard": dict(gun=562, ammo=866),    # 56,2%; munição como no prédio (86,6%)
                       "barrel": dict(gun=12, ammo=62),
                       "barrel_hard": dict(gun=20, ammo=114)},
    "pharmacy":       {"chest": dict(), "chest_hard": dict(),
                       "barrel": dict(), "barrel_hard": dict()},
    "house":          {"chest": dict(), "chest_hard": dict(),
                       "barrel": dict(), "barrel_hard": dict()},
    "workshop":       {"chest": dict(ammo=40), "chest_hard": dict(ammo=70),
                       "barrel": dict(ammo=15), "barrel_hard": dict(ammo=30)},
    "gas_station":    {"chest": dict(), "chest_hard": dict(),
                       "barrel": dict(), "barrel_hard": dict()},
}
# sorteios independentes por rolagem do container (a cura, a comida etc. têm um pool por item)
CORE_POOLS = (("gun",), ("att",), ("ammo",))

# RARIDADE DAS ARMAS (reformulada em 17 Nov 2026, pedido do usuário, "Opção A"): 7 categorias (o DMR do TACZ conta como
# fuzil) e 5 níveis fixos.
# - A chance TOTAL de cada categoria vem do usuário (prédio): "1 a cada N baús" em GUN_CAT_ONE_IN; a divisão entre as
# categorias é proporcional a 1/N. A delegacia usa a MESMA divisão (a chance de arma dela é 2x a do prédio, ver RATES).
# - Dentro da categoria, o peso de CADA arma depende só do nível (LEVEL_W, igual em todas as categorias: cada nível vale
# metade do anterior).
GUN_CAT_ONE_IN = dict(pistol=25, smg=29, rifle=42, shotgun=42, mg=65, sniper=60, rpg=70)
GUN_TYPE_MERGE = {"dmr": "rifle"}
GUN_WEIGHT_TOTAL = 100000  # soma dos pesos das armas na tabela de escolha (só a proporção importa)
LEVEL_W = dict(Comum=16, Incomum=8, Raro=4, Épico=2, Lendário=1)
# nível -> armas (nomes do arquivo do usuário; deagle_golden e springfield1873 não estavam nele: escolha minha,
# aprovada)
GUN_LEVELS = {
    "pistol":  dict(Comum="glock_17 cz75 taurus943 m9a4", Incomum="m1911 b93r hk_mk23 tec_9",
                    Raro="p320 lonetrail rhino357", Épico="taurus500 deagle timeless50 deagle_golden"),
    "smg":     dict(Comum="hk_mp7a1", Incomum="uzi hk_mp5a5", Raro="ump45 p90", Épico="vector45"),
    "rifle":   dict(Comum="m1866 g36k", Incomum="ak47 type_81 m16a1 m16a4 scar_l",
                    Raro="m4a1 hk_g3 qr_24 ak12 qbz_191 urgi hk416d aug mk18 qbz_95",
                    Épico="sks_tactical mk14 scar_h fn_fal mcx_spear_lt spr15hb", Lendário="hcar scar_mk20 ak74m"),
    "shotgun": dict(Comum="db_short", Incomum="db_long", Raro="m1897 m870", Épico="spas_12 aa12", Lendário="m1014"),
    "mg":      dict(Incomum="m249", Raro="rpk", Épico="fn_evolys pkm", Lendário="minigun"),
    "sniper":  dict(Comum="m700", Incomum="svd kar98 springfield1873", Raro="mrad", Épico="ai_awp",
                    Lendário="m95 m107 hm50b"),
    "rpg":     dict(Épico="rpg7 m320"),
}
# MUNIÇÃO JÁ NA ARMA (pedido do usuário, 16 Nov 2026): toda arma nasce com GUN_SPAWN_AMMO_FRACTION do pente cheio
# (ammo_amount do TACZ), arredondado para CIMA (pente de 1 -> 1; 17 -> 9), exceto as de GUN_SPAWN_AMMO_EXCLUDED
# (minigun: sem tamanho de pente definido; nasce com 0).
GUN_SPAWN_AMMO_FRACTION = 0.5
GUN_SPAWN_AMMO_EXCLUDED = ("minigun",)

# MUNIÇÃO (escolhas do usuário, 14-17 Nov 2026): a quantidade por pilha é proporcional à pilha máxima do calibre,
# tomando o 9mm como referência (24 a 50 balas). Qual calibre sai: peso por NÍVEL dado pelo usuário (tacz_ammo.nbt ->
# docs/ammo_rarity.json). A arma NÃO traz munição junto: a munição é um sorteio separado.
AMMO_REF = ("9mm", 24, 50)
# peso por calibre (17 Nov 2026, "pesos 16/8/4/2/1"; Lendário 1 -> 1,35 no mesmo dia: .50 BMG de 1/134 para 1/100 baús
# de prédio); o nível de cada calibre está em docs/ammo_rarity.json
AMMO_LEVEL_W = {"Comum": 16, "Incomum": 8, "Raro": 4, "Épico": 2, "Lendário": 1.35}
# Cada vez que um container "ganha munição" (RATES[...]["ammo"]) saem AMMO_STACKS sorteios de calibre (1 a 3 pilhas; o
# mesmo calibre pode repetir), cada pilha com AMMO_SIZE do tamanho original (9mm 24-50). Pedido do usuário (15 Nov 2026,
# opção C): de 1 a 3 pilhas e o tamanho IGUAL ao original. Consequência: com média de 2,0 pilhas por acerto o TOTAL de
# balas por container dobra em relação a 1 pilha; para manter o total, baixar a chance de munição em RATES (x0,5). Ao
# abrir o container o Minecraft divide as pilhas em pedaços espalhados pelos slots (shuffleAndSplitItems).
AMMO_STACKS = (1, 3)
AMMO_SIZE = 1.0
# .50 BMG: pedido do usuário, 17 Nov 2026 (antes 12-25, proporcional à pilha de 30)
AMMO_RANGE_OVERRIDE = {"50bmg": (21, 30)}

# ATTACHMENTS (redefinidos em 17 Nov 2026, arquivo do usuário "TACZ_attachments.txt" + estruturas .nbt dele): a chance
# de QUALQUER attachment num container é ATT_FRACTION_OF_GUN (1,2: "em torno de 20% mais comuns que armas") da chance de
# arma do mesmo tema e tier. Qual sai: peso por NÍVEL de cada attachment (docs/attachments_rarity.json, gerado por
# tools/att_from_nbt.py a partir da cor do concreto sobre os baús do usuário). "Sem raridade" = baú sem concreto = peso
# do Incomum (opção B).
ATT_FRACTION_OF_GUN = 1.2
ATT_LEVEL_W = {"Comum": 16, "Incomum": 8, "Raro": 4, "Épico": 2, "Lendário": 1, "Mítico": 0.5, "Sem raridade": 8}

# CURA LESRAISINS (escolha do usuário, 15 Nov 2026): chance de CADA item por container, independente dos outros
# (‰: 195 = 19,5%), a mesma em todos os temas e tipos de container, exceto na farmácia (valores fixos em
# HEAL_PHARMACY_FIXED).
# Classes atuais (16 Nov 2026): Comuns = vaseline, ibuprofen, amoxicillin, golden star; Incomuns = blood pack, CAR;
# Raros = AI-2, CMS; Épico = SURV12.
# SURV12: 3% pedido pelo usuário, depois "diminuir levemente a raridade" (= um pouco mais comum): 4%.
# Os 4 Comuns têm a MESMA chance (184‰ = média dos antigos 195/190/180/170, mantendo o total dos Comuns; 15 Nov 2026).
# 16 Nov 2026 (reclassificação pedida pelo usuário): CMS e AI-2 (e Morphine no First Aid) passam a Raro; SURV12 (e
# Morphine Injector) passam a ÉPICO. Valores base (antes dos fatores abaixo): Raro 4,0%, Épico 2,0% (escolha minha).
HEAL_LR = dict(vaseline=184, ibuprofen=184, amoxycillin=184, goldenstar=184, blood_pack=90, carfak=85, ai2=40, cms=40,
               surv12=20)
# Fator geral sobre as chances de cura LesRaisins acima (15 Nov 2026: "exagerei um pouco" -> opção C, tudo x0,5). Não
# vale na farmácia (HEAL_PHARMACY_FIXED). Não mexe no leite, no pão nem no First Aid. Arredondado em ‰ (19,5% -> 9,8%).
HEAL_SCALE = 0.5
# "Duplique a raridade dos itens de cura" (16 Nov 2026) = chances x0,5, em LesRaisins e First Aid, FORA da farmácia.
HEAL_RARITY_SCALE = 0.5
# Temas SEM itens de cura (LesRaisins e First Aid), pedido do usuário em 16 Nov 2026. O leite condensado (comida)
# continua.
HEAL_EXCLUDED_THEMES = ("workshop", "gas_station", "police_station")
# FARMÁCIA "como está" (pedido do usuário): valores CONGELADOS nos números de antes da reclassificação e dos fatores
# (‰).
HEAL_PHARMACY_FIXED = dict(
    lr=dict(vaseline=92, ibuprofen=92, amoxycillin=92, goldenstar=92, blood_pack=90, carfak=85, ai2=80, cms=70,
            surv12=40),
    fa=dict(plaster=150, bandage=92, adrenaline_injector=92, painkillers=92, morphine=82, defibrillator=82,
            morphine_injector=40))

# COMIDA: chance por container (‰) e quantidade; themes=None = todos os temas. O pão é vanilla (exceção explícita do
# usuário) e só em casas. 17 Nov 2026: leite 8% -> 4%, pão 20% -> 16% e 4-12 -> 1-5 (baú; barril = metade).
FOOD = dict(condensed_milk=dict(p=40, lo=1, hi=3, themes=("building", "house")),
            bread=dict(p=160, lo=1, hi=5, themes=("house",)))

# FIRST AID (opcional; tabela à parte com neoforge:mod_loaded). Escolha do usuário, 15-16 Nov 2026: chance de CADA item
# por container (‰), independente dos outros, a mesma em todos os temas exceto na farmácia (HEAL_PHARMACY_FIXED):
# Comum = 9,2% (igual aos comuns LR); Incomum = 4,1% (média dos incomuns LR); Raro = 2,0%; Muito comum = 15%
# (valor meu). 16 Nov 2026: Morphine passa a Raro (base 2,0%) e Morphine Injector a Épico (base 1,0%); depois
# HEAL_RARITY_SCALE (x0,5) fora da farmácia.
# Classes atuais: Muito comum = plaster; Comum = bandage, adrenaline injector, painkillers; Incomum = defibrillator;
# Raro = morphine; Épico = morphine injector.
FA_CHANCE = dict(plaster=150, bandage=92, adrenaline_injector=92, painkillers=92, morphine=20, defibrillator=41,
                 morphine_injector=10)
# quantidade por pilha (pedido do usuário: plaster 4-14 e bandage 2-10; a pilha máxima desses dois no First Aid é 16)
FA_COUNT = dict(plaster=(4, 14), bandage=(2, 10), painkillers=(1, 1), morphine=(1, 1), morphine_injector=(1, 1),
                adrenaline_injector=(1, 1), defibrillator=(1, 1))

# EQUIPAMENTO LESRAISINS (granadas, C4 e armas brancas), pedido do usuário em 16 Nov 2026: chance de CADA item por
# container, baseada nas curas da LesRaisins (já com o x0,5): Comum = 9,2% (M67), Incomum = 4,1% (RGN, média dos
# incomuns de cura), Meio-termo = 3,0% (C4, ponto médio entre o incomum e o raro), Raro = 2,0% cada (Dagger, Karambit;
# igual ao SURV12). M67 sempre 3 a 5 e RGN 2 a 4 (pilha máxima das granadas = 3: o Minecraft divide o excedente em outra
# pilha). O detonator NÃO entra: o C4 o entrega ao ser arremessado (confirmado pelo usuário no jogo). Sem
# smoke/flash/molotov/flash shield. Taco de baseball: 20 -> 15 (18 Nov 2026, "levemente mais raro que a dagger").
GEAR = dict(m67=dict(item="throwable", key="ThrowableId", p=92, lo=3, hi=5),
            rgn=dict(item="throwable", key="ThrowableId", p=41, lo=2, hi=4),
            c4=dict(item="throwable", key="ThrowableId", p=30, lo=1, hi=1),
            dagger=dict(item="melee", key="MeleeWeaponId", p=20, lo=1, hi=1),
            karambit=dict(item="melee", key="MeleeWeaponId", p=20, lo=1, hi=1),
            baseball_bat=dict(item="melee", key="MeleeWeaponId", p=15, lo=1, hi=1))
GEAR_EXCLUDED_THEMES = ("pharmacy",)
# THROWABLES (M67, RGN, C4) só no prédio e na delegacia (pedido do usuário, 18 Nov 2026); as armas brancas continuam em
# todos os temas menos a farmácia.
THROWABLE_THEMES = ("building", "police_station")
# Multiplicador por tema e tipo de item (pedido do usuário, 16 Nov 2026): na delegacia as chances dos THROWABLE dobram.
GEAR_THEME_MULT = {"police_station": {"throwable": 2.0}}

# BARRIS (pedido do usuário, 16 Nov 2026): nos tiers barrel e barrel_hard a chance de cura LesRaisins, First Aid,
# comida, equipamento, ferramentas, caixas de munição e lanternas é BARREL_ITEM_MULT da chance do baú, em TODOS os temas
# (inclusive a farmácia, que é quase só barril). Armas, munição e attachments têm a sua própria redução (RATES); as
# mochilas têm barrel_mult próprio (LEVEL_FAMILIES).
BARREL_ITEM_MULT = 0.5

# CAIXAS DE MUNIÇÃO do TACZ (pedido do usuário, 17 Nov 2026, "Opção B, apenas prédios e delegacia, delegacia com as
# mesmas chances"): tacz:ammo_box vazia; o nível é o custom_data Level (0 ferro, 1 ouro, 2 diamante, como nas receitas
# do TACZ; SNBT em texto para o Level ser INTEIRO). Chance de CADA caixa por baú ("1 a cada N", os mesmos números das
# mochilas: Incomum 14, Raro 20, Épico 30); baú difícil = baú. O TACZ é dependência obrigatória: sem condição de mod.
AMMO_BOX = dict(iron_ammo_box=dict(level=0, one_in=14, themes=("building", "police_station")),       # Incomum
                gold_ammo_box=dict(level=1, one_in=20, themes=("building", "police_station")),       # Raro
                diamond_ammo_box=dict(level=2, one_in=30, themes=("building", "police_station")))    # Épico

# ITENS POR NÍVEL DE MODS OPCIONAIS (mochilas do Sophisticated Backpacks e lanternas do TCT Flashlight; pedido do
# usuário, 17 Nov 2026; níveis das estruturas backpacks.nbt e flashlight.nbt dele). "1 a cada N" é a chance, por baú, de
# CADA ITEM (correção do usuário, 17 Nov 2026); cada item é um sorteio independente. Só nas casas ("itens exclusivos das
# casas"); baú e baú difícil iguais. Cada família tem tabelas e loot modifiers próprios com a condição
# neoforge:mod_loaded (mod ausente = nada acontece).
# (vagas de upgrade, espaços) de cada mochila, como nos baús do usuário
BACKPACK_COMPONENTS = {"copper_backpack": (1, 45), "iron_backpack": (2, 54), "gold_backpack": (3, 81),
                       "diamond_backpack": (5, 108), "netherite_backpack": (7, 120)}
# item -> (nível, "1 a cada N" de CADA item por baú). Mochilas: valores POR ITEM de 18 Nov 2026 (antes por nível
# 9/14/20/30/54); Inception Upgrade REMOVIDO. barrel_mult: 18 Nov 2026, nos barris a MESMA chance do baú; as lanternas
# seguem com BARREL_ITEM_MULT.
LEVEL_FAMILIES = {
    "backpacks": dict(mod="sophisticatedbackpacks", themes=("house",), barrel_mult=1.0,
                      items={"copper_backpack": ("Comum", 13), "iron_backpack": ("Incomum", 20),
                             "gold_backpack": ("Raro", 32), "diamond_backpack": ("Épico", 45),
                             "netherite_backpack": ("Lendário", 57),
                             "stack_upgrade_tier_1": ("Incomum", 26), "stack_upgrade_tier_2": ("Raro", 52),
                             "stack_upgrade_tier_3": ("Épico", 63), "stack_upgrade_tier_4": ("Lendário", 79),
                             "advanced_pickup_upgrade": ("Raro", 29)}),
    "flashlight": dict(mod="flashlight", themes=("house",),   # 17 Nov 2026 (antes 30/45)
                       items={"flashlight_off": ("Incomum", 10), "headlamp_helmet": ("Raro", 16),
                              "night_vision_goggles_helmet": ("Raro", 16)}),
}

# FERRAMENTAS VANILLA na oficina (pedido do usuário, 16 Nov 2026; opção A: metade da chance nos barris). Chance por
# container (‰) no baú: Raro = 1,0% (picareta de ferro e isqueiro, durabilidade restante 40-65%); Lendário = 0,05%
# (picareta de netherite inteira; classe nova, 10x mais rara que o Épico).
TOOLS = dict(iron_pickaxe=dict(p=10, dur=(0.40, 0.65), themes=("workshop",)),
             flint_and_steel=dict(p=10, dur=(0.40, 0.65), themes=("workshop",)),
             netherite_pickaxe=dict(p=0.5, dur=None, themes=("workshop",)))

# SUCATA: o mod sobrescreve as 36 tabelas do AMC (mesmos caminhos) para que NÃO reste nenhum item vanilla útil.
# Só entra aqui o que tem pouca ou nenhuma utilidade: nome -> (peso, mín, máx). A mesma lista em todos os temas.
JUNK = dict(stick=(12, 1, 6), wheat_seeds=(10, 1, 4), beetroot_seeds=(8, 1, 4), melon_seeds=(8, 1, 4),
            pumpkin_seeds=(8, 1, 4), rotten_flesh=(10, 1, 3), bone=(8, 1, 3), paper=(8, 1, 4), bowl=(6, 1, 2),
            glass_bottle=(6, 1, 2), spider_eye=(4, 1, 1))
# quanto de sucata por container: (chance de ter algo em ‰, mín, máx de pilhas). Sem efeito de Sorte (sucata não é
# prêmio). Os tiers _hard têm a mesma sucata: o prêmio dos difíceis vem do mod.
JUNK_SHAPE = {"chest": (1000, 2, 4), "chest_hard": (1000, 2, 4), "barrel": (300, 1, 2), "barrel_hard": (300, 1, 2),
              "pot": (300, 1, 1), "pot_hard": (300, 1, 1)}

# resolução dos sorteios por item: peso total PER_MILLE x ITEM_RES (a chance p, em ‰, pode ser fracionária:
# 0,25‰ = 0,025%)
ITEM_RES = 100
# =====================================================================================================================

# attachments: chance derivada da chance de arma (ATT_FRACTION_OF_GUN), em todo tema/tier que tem armas
for _th in RATES.values():
    for _r in _th.values():
        if "gun" in _r and "att" not in _r:
            _r["att"] = round(_r["gun"] * ATT_FRACTION_OF_GUN)

GUN_LEVEL = {g: (cat, lv) for cat, d in GUN_LEVELS.items() for lv, gs in d.items() for g in gs.split()}
PICK = {"gun": "gun_default", "ammo": "ammo_default", "att": "att"}   # categoria -> tabela de escolha (pick/...)


def load(p):
    """Lê um JSON relativo à raiz do projeto."""
    with open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return json.load(f)


TZ = load("docs/tacz_catalog.json")
CONT = load("docs/containers.json")


# ---------------------------------------------------------------- escolha dos itens
def eligible_guns():
    """Armas que entram no loot: as que têm receita na mesa de armeiro do pacote padrão do TACZ."""
    return {g: v for g, v in TZ["guns"].items() if v["craftable"]}


def gun_weights():
    """Peso de cada arma (soma ~GUN_WEIGHT_TOTAL): fatia da categoria x LEVEL_W do nível / soma dos níveis dela."""
    guns = eligible_guns()
    cat_share = {c: 1.0 / n for c, n in GUN_CAT_ONE_IN.items()}
    tot = sum(cat_share.values())
    cat_share = {c: v / tot for c, v in cat_share.items()}
    for g, v in guns.items():
        assert GUN_LEVEL[g][0] == GUN_TYPE_MERGE.get(v["type"], v["type"]), \
            "categoria do nível != categoria do TACZ: " + g
    sums = {c: sum(LEVEL_W[GUN_LEVEL[g][1]] for g in guns if GUN_LEVEL[g][0] == c) for c in cat_share}
    return {g: max(1, round(GUN_WEIGHT_TOTAL * cat_share[GUN_LEVEL[g][0]] * LEVEL_W[GUN_LEVEL[g][1]]
                            / sums[GUN_LEVEL[g][0]]))
            for g in guns}


def ammo_weights():
    """Peso de cada calibre pelo NÍVEL que o usuário deu (docs/ammo_rarity.json), AMMO_LEVEL_W x100.

    Só calibres com arma elegível (7.62x25 e 6.8x51 Fury não têm arma no loot e o usuário não os classificou)."""
    rar = load("docs/ammo_rarity.json")
    ids = [r["id"] for r in rar]
    assert len(ids) == len(set(ids)) and set(ids) == {v["ammo"].split(":")[1] for v in eligible_guns().values()}, \
        "calibres do arquivo != calibres das armas: rode tools/att_from_nbt.py"
    return {r["id"]: round(AMMO_LEVEL_W[r["level"]] * 100) for r in sorted(rar, key=lambda r: r["id"])}


def ammo_range(c):
    """Mín e máx de balas por pilha: proporcional à pilha máxima, com o 9mm de referência (AMMO_REF)."""
    if c in AMMO_RANGE_OVERRIDE:
        return AMMO_RANGE_OVERRIDE[c]
    ref, lo9, hi9 = AMMO_REF
    base = TZ["ammo"][ref]["stack"]
    st = TZ["ammo"][c]["stack"] or 30
    lo = max(1, int(lo9 * st / base * AMMO_SIZE + 0.5))
    return lo, max(lo, int(hi9 * st / base * AMMO_SIZE + 0.5))


def att_weights():
    """Peso de cada attachment pelo nível (docs/attachments_rarity.json), x100 para caber em inteiros (Mítico 0,5)."""
    rar = load("docs/attachments_rarity.json")
    ids = [r["id"] for r in rar]
    assert len(ids) == len(set(ids)) and set(ids) <= set(TZ["attachments"]), \
        "attachments do arquivo repetidos ou fora do catálogo do TACZ"
    return {r["id"]: round(ATT_LEVEL_W[r["level"]] * 100) for r in rar}


# ---------------------------------------------------------------- JSON dos itens
def custom(**kw):
    """Função de loot que grava `kw` no componente minecraft:custom_data (objeto JSON)."""
    return {"function": "minecraft:set_components", "components": {"minecraft:custom_data": kw}}


def count(lo, hi):
    """Função de loot de quantidade: fixa (lo == hi) ou sorteada entre lo e hi."""
    return {"function": "minecraft:set_count",
            "count": lo if lo == hi else {"type": "minecraft:uniform", "min": lo, "max": hi}}


def gun_spawn_ammo(g):
    """Balas no pente com que a arma nasce (GunCurrentAmmoCount)."""
    mag = TZ["guns"][g]["mag"]
    if g in GUN_SPAWN_AMMO_EXCLUDED or not mag:
        return 0
    return int(mag * GUN_SPAWN_AMMO_FRACTION + 0.5)


def e_gun(g):
    """Entrada de uma arma do TACZ.

    custom_data em TEXTO NBT (SNBT), não em objeto JSON: o Minecraft converte um número JSON pequeno em BYTE ("5b"), e
    o TACZ só lê o pente se GunCurrentAmmoCount for INTEIRO (GunItemDataAccessor: contains(key, 3)). Em SNBT "5" é
    inteiro; "0b" é o booleano da bala na câmara."""
    snbt = '{GunId:"tacz:%s",GunFireMode:"%s",GunCurrentAmmoCount:%d,HasBulletInBarrel:0b}' % (
        g, TZ["guns"][g]["fire_mode"][0], gun_spawn_ammo(g))
    return {"type": "minecraft:item", "name": "tacz:modern_kinetic_gun",
            "functions": [{"function": "minecraft:set_components", "components": {"minecraft:custom_data": snbt}}]}


def e_ammo(c):
    """Entrada de uma pilha de munição do calibre `c`, com a quantidade de ammo_range."""
    lo, hi = ammo_range(c)
    return {"type": "minecraft:item", "name": "tacz:ammo", "functions": [custom(AmmoId="tacz:" + c), count(lo, hi)]}


def e_att(a):
    """Entrada de um attachment do TACZ."""
    return {"type": "minecraft:item", "name": "tacz:attachment", "functions": [custom(AttachmentId="tacz:" + a)]}


def e_lr(i, lo, hi):
    """Entrada de um consumível da LesRaisins (cura ou leite condensado)."""
    return {"type": "minecraft:item", "name": "lrtactical:consumable",
            "functions": [custom(ConsumableId="lrtactical:" + i)] + ([count(lo, hi)] if hi > 1 else [])}


def e_fa(i):
    """Entrada de um item do First Aid, com a quantidade de FA_COUNT."""
    lo, hi = FA_COUNT[i]
    return {"type": "minecraft:item", "name": "firstaid:" + i, "functions": [count(lo, hi)] if hi > 1 else []}


def e_gear(i):
    """Entrada de uma granada/C4 (lrtactical:throwable) ou arma branca (lrtactical:melee)."""
    d = GEAR[i]
    return {"type": "minecraft:item", "name": "lrtactical:" + d["item"],
            "functions": [custom(**{d["key"]: "lrtactical:" + i})] + ([count(d["lo"], d["hi"])] if d["hi"] > 1 else [])}


def e_tool(i):
    """Entrada de uma ferramenta vanilla; set_damage usa a fração de durabilidade RESTANTE (1,0 = inteira)."""
    d = TOOLS[i]
    e = {"type": "minecraft:item", "name": "minecraft:" + i}
    if d["dur"]:
        e["functions"] = [{"function": "minecraft:set_damage",
                           "damage": {"type": "minecraft:uniform", "min": d["dur"][0], "max": d["dur"][1]}}]
    return e


def e_ammo_box(i):
    """Entrada de uma caixa de munição vazia do TACZ; Level em SNBT para ser INTEIRO."""
    return {"type": "minecraft:item", "name": "tacz:ammo_box",
            "functions": [{"function": "minecraft:set_components",
                           "components": {"minecraft:custom_data": "{Level:%d}" % AMMO_BOX[i]["level"]}}]}


def e_family_item(fam, i):
    """Entrada de um item de família opcional (mochila/upgrade ou lanterna); mochilas com vagas e espaços."""
    e = {"type": "minecraft:item", "name": "%s:%s" % (LEVEL_FAMILIES[fam]["mod"], i)}
    if i in BACKPACK_COMPONENTS:
        up, inv = BACKPACK_COMPONENTS[i]
        e["functions"] = [{"function": "minecraft:set_components",
                           "components": {"sophisticatedcore:number_of_upgrade_slots": up,
                                          "sophisticatedcore:number_of_inventory_slots": inv}}]
    return e


def e_item(kind, i):
    """Entrada de um item com chance própria, pelo tipo devolvido por item_chances/fa_chances."""
    if kind == "tool":
        return e_tool(i)
    if kind == "box":
        return e_ammo_box(i)
    if kind == "gear":
        return e_gear(i)
    if kind == "fa":
        return e_fa(i)
    if i == "bread":
        return {"type": "minecraft:item", "name": "minecraft:bread",
                "functions": [count(FOOD["bread"]["lo"], FOOD["bread"]["hi"])]}
    if i == "condensed_milk":
        return e_lr(i, FOOD[i]["lo"], FOOD[i]["hi"])
    return e_lr(i, 1, 1)


# ---------------------------------------------------------------- tabelas e pools
def table(pools, cond=None):
    """Loot table do tipo chest; `cond` = condições do NeoForge (ex.: mod_loaded)."""
    t = {"type": "minecraft:chest", "pools": pools}
    if cond:
        t = {"neoforge:conditions": cond, **t}
    return t


def pool(entries, rolls=1, bonus=None):
    """Pool de loot; bonus = bonus_rolls (omitido quando None)."""
    p = {"rolls": rolls, "entries": entries}
    if bonus is not None:
        p["bonus_rolls"] = bonus
    return p


def with_w(e, w):
    """Cópia da entrada `e` com peso `w`."""
    return {**e, "weight": w}


def pick_tables():
    """Tabelas de escolha (o que sai quando a categoria é sorteada). Nome -> (JSON, condição ou None)."""
    out = {}
    # os nomes "_default" ficam por compatibilidade (eram de quando a delegacia tinha um perfil próprio)
    out["pick/gun_default"] = (table([pool([with_w(e_gun(g), w) for g, w in gun_weights().items()])]), None)
    out["pick/ammo_default"] = (table([pool([with_w(e_ammo(c), w) for c, w in ammo_weights().items()],
                                            {"type": "minecraft:uniform",
                                             "min": AMMO_STACKS[0], "max": AMMO_STACKS[1]})]), None)
    out["pick/att"] = (table([pool([with_w(e_att(a), w) for a, w in att_weights().items()])]), None)
    return out


def junk_tables():
    """Tabelas do AMC sobrescritas, só com sucata. Nome 'tema/tier' -> JSON (namespace abandonedmoderncity)."""
    ents = []
    for i, (w, lo, hi) in JUNK.items():
        e = {"type": "minecraft:item", "name": "minecraft:" + i, "weight": w}
        if hi > 1:
            e["functions"] = [count(lo, hi)]
        ents.append(e)
    out = {}
    for theme in RATES:
        for tier, (chance, lo, hi) in JUNK_SHAPE.items():
            p = {"rolls": lo if lo == hi else {"type": "minecraft:uniform", "min": lo, "max": hi},
                 "bonus_rolls": 0.0, "entries": ents}
            if chance < PER_MILLE:
                p["conditions"] = [{"condition": "minecraft:random_chance", "chance": chance / PER_MILLE}]
            out["%s/%s" % (theme, tier)] = table([p])
    return out


def item_chances(theme, tier="chest"):
    """Itens com chance própria neste tema/tier: lista de (tipo, item, p em ‰).

    Farmácia: cura com valores fixos; barris: x BARREL_ITEM_MULT."""
    out = []
    for i, p in ({} if theme in HEAL_EXCLUDED_THEMES else HEAL_LR).items():
        v = HEAL_PHARMACY_FIXED["lr"][i] if theme == "pharmacy" else int(p * HEAL_SCALE * HEAL_RARITY_SCALE + 0.5)
        out.append(("lr", i, max(1, min(PER_MILLE, v))))
    for i, f in FOOD.items():
        if f["themes"] is None or theme in f["themes"]:
            out.append(("food", i, f["p"]))
    for i, d in TOOLS.items():
        if theme in d["themes"]:
            out.append(("tool", i, d["p"]))
    for i, d in AMMO_BOX.items():
        if theme in d["themes"]:
            out.append(("box", i, PER_MILLE / d["one_in"]))
    if theme not in GEAR_EXCLUDED_THEMES:
        for i, d in GEAR.items():
            if d["item"] == "throwable" and theme not in THROWABLE_THEMES:
                continue
            m = GEAR_THEME_MULT.get(theme, {}).get(d["item"], 1.0)
            out.append(("gear", i, min(PER_MILLE, round(d["p"] * m))))
    if tier.startswith("barrel"):
        out = [(k, i, p * BARREL_ITEM_MULT) for k, i, p in out]
    return out


def fa_chances(theme, tier="chest"):
    """First Aid neste tema/tier: lista de (item, p em ‰).

    Farmácia: valores congelados (HEAL_PHARMACY_FIXED); fora dela, chance x HEAL_RARITY_SCALE;
    barris: x BARREL_ITEM_MULT."""
    if theme in HEAL_EXCLUDED_THEMES:
        return []
    out = []
    for i, p in FA_CHANCE.items():
        v = HEAL_PHARMACY_FIXED["fa"][i] if theme == "pharmacy" else int(p * HEAL_RARITY_SCALE + 0.5)
        out.append((i, max(1, min(PER_MILLE, v))))
    if tier.startswith("barrel"):
        out = [(i, p * BARREL_ITEM_MULT) for i, p in out]
    return out


def family_chances(fam, theme, tier):
    """[(item, nível, chance do item em ‰)] do tema/tier ([] se a família não vale no tema)."""
    f = LEVEL_FAMILIES[fam]
    if theme not in f["themes"]:
        return []
    m = f.get("barrel_mult", BARREL_ITEM_MULT) if tier.startswith("barrel") else 1.0
    return [(i, lv, PER_MILLE / n * m) for i, (lv, n) in f["items"].items()]


def chance_pool(entry, p, rolls=1, bonus=None):
    """Um sorteio independente: `entry` com chance p (‰, aceita fração) ou nada.

    A Sorte sobe a chance pelo `quality` (LUCK_QUALITY), como nas categorias de RATES. Chance de 100%: sem `empty`."""
    w = max(1, round(p * ITEM_RES))
    q = max(1, round(w * LUCK_QUALITY))
    ents = [{**entry, "weight": w, "quality": q}]
    if w < PER_MILLE * ITEM_RES:
        ents.append({"type": "minecraft:empty", "weight": PER_MILLE * ITEM_RES - w, "quality": -q})
    return pool(ents, rolls, bonus)


def item_pool(kind, i, p):
    """Sorteio independente de um item de item_chances/fa_chances (com bonus_rolls 0.0, como sempre foi)."""
    return chance_pool(e_item(kind, i), p, 1, 0.0)


def family_pool(fam, i, p):
    """Sorteio independente de um item de família opcional (sem bonus_rolls)."""
    return chance_pool(e_family_item(fam, i), p)


def weights(rates):
    """(weight, quality) por categoria + empty, somando PER_MILLE em Sorte 0 e mantendo ~PER_MILLE com Sorte

    (quality do empty é o negativo da soma das outras)."""
    res = {}
    for c, w in rates.items():
        res[c] = (w, max(1, round(w * LUCK_QUALITY)))
    res["empty"] = (PER_MILLE - sum(w for w, _ in res.values()), -sum(q for _, q in res.values()))
    return res


def main_tables():
    """Para cada tema/tier: tabela principal (core), do First Aid e das famílias opcionais. Nome -> JSON."""
    out = {}
    for theme, tiers in RATES.items():
        for tier, rates in tiers.items():
            rolls, bonus = ROLLS[tier]
            pools = []
            for group in CORE_POOLS:
                part = {k: v for k, v in rates.items() if k in group}
                if not part:
                    continue
                ent = []
                for c, (w, q) in weights(part).items():
                    if c == "empty" and w <= 0:
                        continue          # chance 100%: sem entrada vazia (peso 0 não vale)
                    if c == "empty":
                        e = {"type": "minecraft:empty"}
                    else:
                        e = {"type": "minecraft:loot_table", "value": "%s:pick/%s" % (MOD, PICK[c])}
                    ent.append({**e, "weight": w, "quality": q})
                pools.append(pool(ent, rolls, bonus))
            for kind, i, p in item_chances(theme, tier):
                pools.append(item_pool(kind, i, p))
            out["%s/%s_core" % (theme, tier)] = table(pools)
            if not fa_chances(theme, tier):
                continue          # tema sem First Aid: sem tabela nem loot modifier
            out["%s/%s_firstaid" % (theme, tier)] = table([item_pool("fa", i, p) for i, p in fa_chances(theme, tier)],
                                                           [{"type": "neoforge:mod_loaded", "modid": "firstaid"}])
    for fam, f in LEVEL_FAMILIES.items():
        for theme in f["themes"]:
            for tier in TIERS:
                pools = [family_pool(fam, i, p) for i, _, p in family_chances(fam, theme, tier)]
                cond = [{"type": "neoforge:mod_loaded", "modid": f["mod"]}]
                out["%s/%s_%s" % (theme, tier, fam)] = table(pools, cond)
    return out


# ---------------------------------------------------------------- esperados (a mesma conta do Minecraft)
def eff(w, q, luck):
    """Peso efetivo de uma entrada com Sorte `luck` (regra do Minecraft: floor(weight + quality*Sorte), mínimo 0)."""
    return max(0, math.floor(w + q * luck))


def item_prob(p, luck):
    """Chance real de um sorteio por item (a mesma conta do Minecraft, na resolução de chance_pool)."""
    w = max(1, round(p * ITEM_RES))
    q = max(1, round(w * LUCK_QUALITY))
    a = eff(w, q, luck)
    e = eff(PER_MILLE * ITEM_RES - w, -q, luck)
    return a / (a + e) if a + e else 0.0


def expected(theme, tier, luck):
    """Esperado por container (Sorte `luck`): gun, ammo, att em pilhas; lr, food, gear, tool, box em sorteios; fa em
    unidades."""
    rates = RATES[theme][tier]
    rolls, bonus = ROLLS[tier]
    r = rolls + math.floor(bonus * luck)
    res = {k: 0.0 for k in ("gun", "ammo", "att", "lr", "fa", "food", "gear", "tool", "box")}
    for cat_set in CORE_POOLS:
        part = {k: v for k, v in rates.items() if k in cat_set}
        if not part:
            continue
        wq = weights(part)
        tot = sum(eff(w, q, luck) for w, q in wq.values())
        for c in part:
            p = eff(*wq[c], luck) / tot if tot else 0
            avg = {"ammo": sum(AMMO_STACKS) / 2}.get(c, 1)
            res[c] += r * p * avg
    for i, p0 in fa_chances(theme, tier):             # First Aid: unidades esperadas (chance x quantidade média)
        res["fa"] += item_prob(p0, luck) * sum(FA_COUNT[i]) / 2
    for kind, i, p0 in item_chances(theme, tier):     # um sorteio por item (rolagem única, sem bonus)
        res[kind] += item_prob(p0, luck)
    return res


def preview():
    """Imprime os esperados por estrutura (docs/containers.json), armas por baú e chance de um baú ter algo do mod."""
    rows = []
    for name, v in CONT.items():
        th = v["theme"]
        if th not in RATES:
            continue
        rows.append((th, name, v))
    rows.sort(key=lambda r: (list(RATES).index(r[0]), -r[2]["total"]))
    print("Esperado por estrutura (uma instância): armas | pilhas de munição | attachments | cura LesRaisins | "
          "cura First Aid")
    print("Sorte 0 detalhada; 'armas' também em Sorte 1/2/3. Vasos não recebem nada do mod.\n")
    print("%-14s %-30s %5s | %s | %-23s | %6s %6s" % ("tema", "estrutura", "cont.", "Sorte 0: arm  mun  att   LR   FA",
                                                     "armas S0 S1 S2 S3", "LR S3", "FA S3"))
    for th, name, v in rows:
        def tot(luck):
            t = {k: 0.0 for k in ("gun", "ammo", "att", "lr", "fa", "food", "gear", "tool", "box")}
            for tier, n in v["tiers"].items():
                if tier.startswith("pot"):
                    continue
                for k, x in expected(th, tier, luck).items():
                    t[k] += n * x
            return t
        e = [tot(lk) for lk in LUCKS]
        print("%-14s %-30s %5d | %17.1f %4.1f %4.1f %4.1f %4.1f | %5.1f %4.1f %4.1f %4.1f | %5.1f %5.1f" % (
            th, name, v["total"], e[0]["gun"], e[0]["ammo"], e[0]["att"], e[0]["lr"], e[0]["fa"],
            e[0]["gun"], e[1]["gun"], e[2]["gun"], e[3]["gun"], e[3]["lr"], e[3]["fa"]))
    print("\nBaús (chest + chest_hard) por arma, Sorte 0 / I / II / III  (1 arma a cada N baús):")
    for th in ("building", "police_station"):
        cells = []
        for lk in LUCKS:
            ex = 0.0
            ch = 0
            for _, _, v in rows:
                if v["theme"] != th:
                    continue
                for tr, c in v["tiers"].items():
                    if tr.startswith("chest"):
                        ex += c * expected(th, tr, lk)["gun"]
                        ch += c
            cells.append("S%d: 1 a cada %.1f" % (lk, ch / ex))
        print("  %-15s %s" % (th, "   ".join(cells)))
    gun_p = []
    for tr, c in CONT["abandoned_police_station"]["tiers"].items():
        if tr.startswith("pot"):
            continue
        gun_p += [expected("police_station", tr, 0)["gun"]] * c
    dist = [1.0]
    for q in gun_p:
        dist = [(dist[k] if k < len(dist) else 0) * (1 - q) + (dist[k - 1] * q if k > 0 else 0)
                for k in range(len(dist) + 1)]
    print("Delegacia, Sorte 0: chance de ter pelo menos N armas: "
          + "  ".join("N=%d: %.0f%%" % (n, 100 * sum(dist[n:])) for n in (3, 4, 5, 6, 7, 8)))
    print("\nChance de UM baú (chest) ter pelo menos 1 item do mod (TACZ+LesRaisins | + First Aid), por tema e Sorte:")
    for th in RATES:
        for tier in ("chest", "chest_hard"):
            cells = []
            for lk in LUCKS:
                rolls, bonus = ROLLS[tier]
                r = rolls + math.floor(bonus * lk)
                p_none = 1.0
                for group in CORE_POOLS:
                    part = {k: v for k, v in RATES[th][tier].items() if k in group}
                    if not part:
                        continue
                    wq = weights(part)
                    tot = sum(eff(w, q, lk) for w, q in wq.values())
                    p_none *= (eff(*wq["empty"], lk) / tot) ** r
                for kind, i, p0 in item_chances(th, tier):
                    p_none *= 1.0 - item_prob(p0, lk)
                p_core = 1 - p_none
                pn_fa = 1.0
                for i, p0 in fa_chances(th, tier):
                    pn_fa *= 1.0 - item_prob(p0, lk)
                p_fa = 1 - pn_fa
                cells.append("S%d %4.0f%%|%4.0f%%" % (lk, 100 * p_core, 100 * (1 - (1 - p_core) * (1 - p_fa))))
            print("  %-14s %-11s %s" % (th, tier, "   ".join(cells)))


# ---------------------------------------------------------------- escrita + verificações
def write_json(path, obj):
    """Grava `obj` como JSON indentado (2 espaços, UTF-8, quebra de linha no fim), criando as pastas."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def write(out=OUT):
    """Grava todas as tabelas e loot modifiers em `out` (padrão: src/main/resources/data) e roda check()."""
    base = os.path.join(out, MOD)
    amc_dir = os.path.join(out, AMC)
    for d in (base, amc_dir):
        if os.path.isdir(d):
            shutil.rmtree(d)
    gl = os.path.join(out, "neoforge/loot_modifiers/global_loot_modifiers.json")
    tables, glms = {}, {}
    for n, (t, _) in pick_tables().items():
        tables[n] = t
    for n, t in main_tables().items():
        tables[n] = t
    for n, t in tables.items():
        write_json("%s/loot_table/%s.json" % (base, n), t)
    junk = junk_tables()
    for n, t in junk.items():
        write_json("%s/loot_table/chests/%s.json" % (amc_dir, n), t)
    for n in main_tables():
        theme, rest = n.split("/")
        tier, kind = rest.rsplit("_", 1)
        g = {"type": "neoforge:add_table",
             "conditions": [{"condition": "neoforge:loot_table_id",
                             "loot_table_id": "%s:chests/%s/%s" % (AMC, theme, tier)}],
             "table": "%s:%s" % (MOD, n)}
        modid = "firstaid" if kind == "firstaid" else LEVEL_FAMILIES[kind]["mod"] if kind in LEVEL_FAMILIES else None
        if modid:
            g["neoforge:conditions"] = [{"type": "neoforge:mod_loaded", "modid": modid}]
        glms["%s_%s_%s" % (kind, theme, tier)] = g
    for n, g in glms.items():
        write_json("%s/loot_modifiers/%s.json" % (base, n), g)
    write_json(gl, {"replace": False, "entries": ["%s:%s" % (MOD, n) for n in glms]})
    check(base, gl, tables, glms, junk)
    print("escrito: %d tabelas, %d loot modifiers, %d tabelas do AMC sobrescritas (só sucata)"
          % (len(tables), len(glms), len(junk)))


def check(base, gl, tables, glms, junk):
    """Verificações de consistência dos arquivos gerados; encerra com erro se algo estiver errado."""
    errs = []
    with open(gl, encoding="utf-8") as f:
        listed = json.load(f)["entries"]
    for e in listed:
        if not os.path.exists("%s/loot_modifiers/%s.json" % (base, e.split(":")[1])):
            errs.append("GLM listado não existe: " + e)
    for n in glms:
        if "%s:%s" % (MOD, n) not in listed:
            errs.append("GLM existe mas não está listado: " + n)
    amc_ids = {"%s:chests/%s/%s" % (AMC, th, ti) for th in RATES for ti in TIERS}
    for n, g in glms.items():
        if g["table"].split(":")[1] not in tables:
            errs.append("GLM aponta para tabela inexistente: " + n)
        if g["conditions"][0]["loot_table_id"] not in amc_ids:
            errs.append("alvo não é tabela do AMC: " + n)
    for n, t in tables.items():
        s = json.dumps(t)
        for mid in ["firstaid"] + [f["mod"] for f in LEVEL_FAMILIES.values()]:
            if '"%s:' % mid in s and t.get("neoforge:conditions") != [{"type": "neoforge:mod_loaded", "modid": mid}]:
                errs.append("item do mod %s em tabela sem condição mod_loaded: %s" % (mid, n))
        if "pot" in n:
            errs.append("tabela de vaso gerada: " + n)
        for ref in [x for x in s.split('"') if x.startswith(MOD + ":pick/")]:
            if ref.split(":")[1] not in tables:
                errs.append("tabela de escolha inexistente: " + ref)
    # nenhum item vanilla fora da lista de sucata, em NENHUMA tabela gerada (mod + sobrescritas do AMC)
    allowed = {"minecraft:" + i for i in JUNK} | {"minecraft:bread"} | {"minecraft:" + i for i in TOOLS}
    for n, t in list(tables.items()) + [("amc:" + k, v) for k, v in junk.items()]:
        for name in re.findall(r'"name": "(minecraft:[a-z_0-9]+)"', json.dumps(t)):
            if name not in allowed:
                errs.append("item vanilla fora da sucata em %s: %s" % (n, name))
    # lista explícita (não derivada de JUNK_SHAPE): se um tier sumir da sucata, a tabela vanilla do AMC voltaria
    # sem aviso
    amc_tiers = ("chest", "chest_hard", "barrel", "barrel_hard", "pot", "pot_hard")
    expect = {"%s/%s" % (th, ti) for th in RATES for ti in amc_tiers}
    if set(junk) != expect:
        errs.append("tabelas do AMC sobrescritas != as 36 do AMC")
    for g, v in TZ["guns"].items():
        if v["ammo"].split(":")[1] not in TZ["ammo"]:
            errs.append("munição da arma %s fora do catálogo" % g)
    if errs:
        print("\n".join("ERRO: " + e for e in errs))
        sys.exit(1)


if __name__ == "__main__":
    preview()
    if "--write" in sys.argv:
        write()
