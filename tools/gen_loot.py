#!/usr/bin/env python3
"""Generator of the AMC TACZ Loot loot tables.

  python3 -I tools/gen_loot.py            -> only prints the PREVIEW (expected loot per structure, Luck 0 to 3)
  python3 -I tools/gen_loot.py --write    -> deletes and rewrites src/main/resources/data/amctaczloot,
                                             src/main/resources/data/abandonedmoderncity and global_loot_modifiers.json
                                             (the generator owns these files)

Input data (in docs/):
  tacz_catalog.json        TACZ guns, ammo and attachments (tools/tacz_catalog.py)
  ammo_rarity.json         level of each caliber (tools/att_from_nbt.py, from the user's .nbt structures)
  attachments_rarity.json  level of each attachment (tools/att_from_nbt.py)
  containers.json          containers per AMC structure, used only by the PREVIEW (tools/measure_containers.py)
  (docs/lr_catalog.json, from tools/lr_catalog.py, is reference only: the generator does not read it)

How Luck works (checked in the Minecraft 1.21.1 bytecode):
  effective weight of an entry = floor(weight + quality * Luck)   (never below 0)
  rolls of a pool              = rolls + floor(bonus_rolls * Luck)
So `quality` is the lever that already responds at Luck I; `bonus_rolls` below 1 only acts from Luck II/III on.
Junk: the mod also OVERRIDES the 36 AMC tables (6 themes x chest/barrel/pot x normal/_hard)
(data/abandonedmoderncity/loot_table/chests/...) with junk only, so no useful vanilla item is left; the mod loads AFTER
the AMC (mods.toml, ordering AFTER).
Decorated pots get no prizes: Minecraft calls unpackLootTable(null) on them (no Luck) and, if a table produces more
stacks than slots, fills until the slots run out and LOSES the rest, picked at random (LootTable.fill: "Tried to
over-fill a container"); a pot has 1 slot, so an item from this mod would compete with the AMC's.
"""
import json, math, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "src/main/resources/data")
AMC = "abandonedmoderncity"
MOD = "amctaczloot"

# =====================================================================================================================
# NUMBERS (everything that can be tuned lives here, down to the "=" line at the end of the block).
#
# Two ways of writing a chance, matching how the user gave the numbers (both stay in use):
#   - in ‰ (per mille) per container, at Luck 0: 92 = 9.2%    -> RATES, HEAL_LR, FA_CHANCE, FOOD, GEAR, TOOLS
#   - "1 in N" chests: 14 = 1/14 = 7.1%                       -> GUN_CAT_ONE_IN, AMMO_BOX, LEVEL_FAMILIES
# In the RATES categories the rest (1000 - sum) is the `empty` entry: the container gets nothing from that category.
# =====================================================================================================================
PER_MILLE = 1000          # scale of the chances in ‰
LUCK_QUALITY = 0.25       # each Luck level multiplies the chance of each category by (1 + 0.25 * Luck)
TIERS = ("chest", "chest_hard", "barrel", "barrel_hard")
LUCKS = (0, 1, 2, 3)      # Luck levels shown in the preview
# rolls per tier: (rolls, bonus_rolls).  floor(bonus*Luck): 0.34 adds 1 roll only at Luck III; 0.2 only at Luck V
ROLLS = {"chest": (1, 0.2), "chest_hard": (1, 0.34), "barrel": (1, 0.0), "barrel_hard": (1, 0.0)}

# chance (‰) per roll of each category, per theme and tier.  gun = gun (no ammo with it),
# ammo = ammo (own pool, 1 to 3 stacks), att = attachment (computed below from gun: ATT_FRACTION_OF_GUN).
# LesRaisins healing, First Aid, food, equipment etc. are NOT here: each item has its own chance per container.
RATES = {
    # BUILDING (17 Nov 2026, "Option A, keep 16.8%"): the user's categories (GUN_CAT_ONE_IN) add up to 16.84% guns per
    # chest (was 12%); the other tiers go up by the same factor (16.84/12 = 1.404).
    # Attachments = ATT_FRACTION_OF_GUN (1.2) x gun: 202 / 337 / 7 / 12 ‰.
    "building":       {"chest": dict(gun=168, ammo=520),          # 1 gun in 5.95 chests; ammo in 52%
                       "chest_hard": dict(gun=281, ammo=866),    # 1 gun in 3.6 hard chests; ammo 86.6%
                       "barrel": dict(gun=6, ammo=62),
                       "barrel_hard": dict(gun=10, ammo=114)},
    # POLICE STATION (17 Nov 2026): the chance of ALL guns is 2x the building's (same split by category and level; chest
    # 33.6%, hard 56.2%, barrels 1.2% / 2.0%). Attachments = 1.2 x gun (= 2x the building's: 403 / 674 / 14 / 24 ‰).
    # Ammo = the SAME chance as the building (17 Nov 2026: 52 / 86.6 / 6.2 / 11.4%).
    "police_station": {"chest": dict(gun=336, ammo=520),          # 1 gun in 3 chests; ammo as in the building (52%)
                       "chest_hard": dict(gun=562, ammo=866),    # 56.2%; ammo as in the building (86.6%)
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
# independent draws per container roll (healing, food etc. have one pool per item)
CORE_POOLS = (("gun",), ("att",), ("ammo",))

# GUN RARITY (reworked on 17 Nov 2026 at the user's request, "Option A"): 7 categories (TACZ's DMR counts as a rifle)
# and 5 fixed levels.
# - The TOTAL chance of each category comes from the user (building): "1 in N chests" in GUN_CAT_ONE_IN; the split
#   between categories is proportional to 1/N. The police station uses the SAME split (its gun chance is 2x the
#   building's, see RATES).
# - Within a category, the weight of EACH gun depends only on its level (LEVEL_W, the same in every category: each level
#   is worth half of the previous one).
GUN_CAT_ONE_IN = dict(pistol=25, smg=29, rifle=42, shotgun=42, mg=65, sniper=60, rpg=70)
GUN_TYPE_MERGE = {"dmr": "rifle"}
GUN_WEIGHT_TOTAL = 100000  # sum of the gun weights in the pick table (only the proportion matters)
LEVEL_W = dict(Comum=16, Incomum=8, Raro=4, Épico=2, Lendário=1)   # Common, Uncommon, Rare, Epic, Legendary
# level -> guns (names from the user's file; deagle_golden and springfield1873 were not in it: my choice, approved)
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
# AMMO ALREADY IN THE GUN (user's request, 16 Nov 2026): every gun spawns with GUN_SPAWN_AMMO_FRACTION of a full
# magazine (TACZ ammo_amount), rounded UP (magazine of 1 -> 1; 17 -> 9), except those in GUN_SPAWN_AMMO_EXCLUDED
# (minigun: no magazine size defined; spawns with 0).
GUN_SPAWN_AMMO_FRACTION = 0.5
GUN_SPAWN_AMMO_EXCLUDED = ("minigun",)

# AMMO (user's choices, 14-17 Nov 2026): the amount per stack is proportional to the caliber's max stack, with 9mm as
# the reference (24 to 50 rounds). Which caliber drops: weight by the LEVEL the user gave (tacz_ammo.nbt ->
# docs/ammo_rarity.json). A gun does NOT come with ammo: ammo is a separate draw.
AMMO_REF = ("9mm", 24, 50)
# weight per caliber (17 Nov 2026, "weights 16/8/4/2/1"; Legendary 1 -> 1.35 the same day: .50 BMG from 1 in 134 to
# 1 in 100 building chests); the level of each caliber is in docs/ammo_rarity.json
AMMO_LEVEL_W = {"Comum": 16, "Incomum": 8, "Raro": 4, "Épico": 2, "Lendário": 1.35}
# Each time a container "gets ammo" (RATES[...]["ammo"]) there are AMMO_STACKS caliber draws (1 to 3 stacks; the same
# caliber can repeat), each stack at AMMO_SIZE of the original size (9mm 24-50). User's request (15 Nov 2026, option C):
# 1 to 3 stacks at the ORIGINAL size. Consequence: with 2.0 stacks per hit on average, the TOTAL rounds per container
# doubles compared with 1 stack; to keep the total, lower the ammo chance in RATES (x0.5). When a container is opened
# Minecraft splits the stacks into pieces spread over the slots (shuffleAndSplitItems).
AMMO_STACKS = (1, 3)
AMMO_SIZE = 1.0
# .50 BMG: user's request, 17 Nov 2026 (was 12-25, proportional to the stack of 30)
AMMO_RANGE_OVERRIDE = {"50bmg": (21, 30)}

# ATTACHMENTS (redefined on 17 Nov 2026 from the user's file "TACZ_attachments.txt" and .nbt structures): the chance of
# ANY attachment in a container is ATT_FRACTION_OF_GUN (1.2: "about 20% more common than guns") times the gun chance of
# the same theme and tier. Which one drops: weight by the LEVEL of each attachment (docs/attachments_rarity.json, made
# by tools/att_from_nbt.py from the concrete color above the user's chests). "Sem raridade" (unrated) = chest without
# concrete = the Uncommon weight (option B).
ATT_FRACTION_OF_GUN = 1.2
ATT_LEVEL_W = {"Comum": 16, "Incomum": 8, "Raro": 4, "Épico": 2, "Lendário": 1, "Mítico": 0.5, "Sem raridade": 8}

# LESRAISINS HEALING (user's choice, 15 Nov 2026): chance of EACH item per container, independent of the others
# (‰: 195 = 19.5%), the same in every theme and container type, except in the pharmacy (fixed values in
# HEAL_PHARMACY_FIXED).
# Current classes (16 Nov 2026): Common = vaseline, ibuprofen, amoxicillin, golden star; Uncommon = blood pack, CAR;
# Rare = AI-2, CMS; Epic = SURV12.
# SURV12: 3% asked by the user, then "lower the rarity a little" (= a little more common): 4%.
# The 4 Common items have the SAME chance (184‰ = mean of the old 195/190/180/170, keeping their total; 15 Nov 2026).
# 16 Nov 2026 (reclassification asked by the user): CMS and AI-2 (and Morphine in First Aid) become Rare; SURV12 (and
# Morphine Injector) become EPIC. Base values (before the factors below): Rare 4.0%, Epic 2.0% (my choice).
HEAL_LR = dict(vaseline=184, ibuprofen=184, amoxycillin=184, goldenstar=184, blood_pack=90, carfak=85, ai2=40, cms=40,
               surv12=20)
# Overall factor on the LesRaisins healing chances above (15 Nov 2026: "I overdid it a little" -> option C, all x0.5).
# Not applied in the pharmacy (HEAL_PHARMACY_FIXED). Does not touch milk, bread or First Aid. Rounded in ‰ (19.5% ->
# 9.8%).
HEAL_SCALE = 0.5
# "Double the rarity of the healing items" (16 Nov 2026) = chances x0.5, in LesRaisins and First Aid, OUTSIDE the
# pharmacy.
HEAL_RARITY_SCALE = 0.5
# Themes WITHOUT healing items (LesRaisins and First Aid), user's request on 16 Nov 2026. Condensed milk (food) stays.
HEAL_EXCLUDED_THEMES = ("workshop", "gas_station", "police_station")
# PHARMACY "as it is" (user's request): values FROZEN at the numbers from before the reclassification and the factors
# (‰).
HEAL_PHARMACY_FIXED = dict(
    lr=dict(vaseline=92, ibuprofen=92, amoxycillin=92, goldenstar=92, blood_pack=90, carfak=85, ai2=80, cms=70,
            surv12=40),
    fa=dict(plaster=150, bandage=92, adrenaline_injector=92, painkillers=92, morphine=82, defibrillator=82,
            morphine_injector=40))

# FOOD: chance per container (‰) and amount; themes=None = every theme. Bread is vanilla (an explicit exception from the
# user) and only in houses. 17 Nov 2026: milk 8% -> 4%, bread 20% -> 16% and 4-12 -> 1-5 (chest; barrel = half).
FOOD = dict(condensed_milk=dict(p=40, lo=1, hi=3, themes=("building", "house")),
            bread=dict(p=160, lo=1, hi=5, themes=("house",)))

# FIRST AID (optional; separate table with neoforge:mod_loaded). User's choice, 15-16 Nov 2026: chance of EACH item per
# container (‰), independent of the others, the same in every theme except the pharmacy (HEAL_PHARMACY_FIXED):
# Common = 9.2% (same as the LR Common items); Uncommon = 4.1% (mean of the LR Uncommon items); Rare = 2.0%;
# Very common = 15% (my value). 16 Nov 2026: Morphine becomes Rare (base 2.0%) and Morphine Injector Epic (base 1.0%);
# then HEAL_RARITY_SCALE (x0.5) outside the pharmacy.
# Current classes: Very common = plaster; Common = bandage, adrenaline injector, painkillers; Uncommon = defibrillator;
# Rare = morphine; Epic = morphine injector.
FA_CHANCE = dict(plaster=150, bandage=92, adrenaline_injector=92, painkillers=92, morphine=20, defibrillator=41,
                 morphine_injector=10)
# amount per stack (user's request: plaster 4-14 and bandage 2-10; the max stack of both in First Aid is 16)
FA_COUNT = dict(plaster=(4, 14), bandage=(2, 10), painkillers=(1, 1), morphine=(1, 1), morphine_injector=(1, 1),
                adrenaline_injector=(1, 1), defibrillator=(1, 1))

# LESRAISINS EQUIPMENT (grenades, C4 and melee weapons), user's request on 16 Nov 2026: chance of EACH item per
# container, based on the LesRaisins healing chances (already x0.5): Common = 9.2% (M67), Uncommon = 4.1% (RGN, mean of
# the healing Uncommon items), In-between = 3.0% (C4, midpoint between Uncommon and Rare), Rare = 2.0% each (Dagger,
# Karambit; same as SURV12). M67 always 3 to 5 and RGN 2 to 4 (grenade max stack = 3: Minecraft splits the excess into
# another stack). The detonator is NOT included: the C4 gives it when thrown (confirmed by the user in game). No
# smoke/flash/molotov/flash shield. Baseball bat: 20 -> 15 (18 Nov 2026, "slightly rarer than the dagger").
GEAR = dict(m67=dict(item="throwable", key="ThrowableId", p=92, lo=3, hi=5),
            rgn=dict(item="throwable", key="ThrowableId", p=41, lo=2, hi=4),
            c4=dict(item="throwable", key="ThrowableId", p=30, lo=1, hi=1),
            dagger=dict(item="melee", key="MeleeWeaponId", p=20, lo=1, hi=1),
            karambit=dict(item="melee", key="MeleeWeaponId", p=20, lo=1, hi=1),
            baseball_bat=dict(item="melee", key="MeleeWeaponId", p=15, lo=1, hi=1))
GEAR_EXCLUDED_THEMES = ("pharmacy",)
# THROWABLES (M67, RGN, C4) only in the building and the police station (user's request, 18 Nov 2026); melee weapons
# stay in every theme except the pharmacy.
THROWABLE_THEMES = ("building", "police_station")
# Multiplier per theme and item type (user's request, 16 Nov 2026): in the police station the THROWABLE chances double.
GEAR_THEME_MULT = {"police_station": {"throwable": 2.0}}

# BARRELS (user's request, 16 Nov 2026): in the barrel and barrel_hard tiers the chance of LesRaisins healing, First
# Aid, food, equipment, tools, ammo boxes and flashlights is BARREL_ITEM_MULT times the chest chance, in EVERY theme
# (including the pharmacy, which is almost all barrels). Guns, ammo and attachments have their own reduction (RATES);
# backpacks have their own barrel_mult (LEVEL_FAMILIES).
BARREL_ITEM_MULT = 0.5

# TACZ AMMO BOXES (user's request, 17 Nov 2026, "Option B, only buildings and police station, police station with the
# same chances"): empty tacz:ammo_box; the level is custom_data Level (0 iron, 1 gold, 2 diamond, as in the TACZ
# recipes;
# SNBT text so Level is an INTEGER). Chance of EACH box per chest ("1 in N", the same numbers as the backpacks:
# Uncommon 14, Rare 20, Epic 30); hard chest = chest. TACZ is a required dependency: no mod condition.
AMMO_BOX = dict(iron_ammo_box=dict(level=0, one_in=14, themes=("building", "police_station")),       # Uncommon
                gold_ammo_box=dict(level=1, one_in=20, themes=("building", "police_station")),       # Rare
                diamond_ammo_box=dict(level=2, one_in=30, themes=("building", "police_station")))    # Epic

# LEVELED ITEMS FROM OPTIONAL MODS (Sophisticated Backpacks backpacks and TCT Flashlight flashlights; user's request,
# 17 Nov 2026; levels from the user's backpacks.nbt and flashlight.nbt structures). "1 in N" is the chance, per chest,
# of
# EACH ITEM (user's correction, 17 Nov 2026); each item is an independent draw. Houses only ("items exclusive to
# houses"); chest and hard chest equal. Each family has its own tables and loot modifiers with the neoforge:mod_loaded
# condition (mod missing = nothing happens).
# (upgrade slots, inventory slots) of each backpack, as in the user's chests
BACKPACK_COMPONENTS = {"copper_backpack": (1, 45), "iron_backpack": (2, 54), "gold_backpack": (3, 81),
                       "diamond_backpack": (5, 108), "netherite_backpack": (7, 120)}
# item -> (level, "1 in N" for EACH item per chest). Backpacks: PER-ITEM values from 18 Nov 2026 (before, per level
# 9/14/20/30/54); Inception Upgrade REMOVED. barrel_mult: 18 Nov 2026, in barrels the SAME chance as in chests; the
# flashlights keep BARREL_ITEM_MULT.
LEVEL_FAMILIES = {
    "backpacks": dict(mod="sophisticatedbackpacks", themes=("house",), barrel_mult=1.0,
                      items={"copper_backpack": ("Comum", 13), "iron_backpack": ("Incomum", 20),
                             "gold_backpack": ("Raro", 32), "diamond_backpack": ("Épico", 45),
                             "netherite_backpack": ("Lendário", 57),
                             "stack_upgrade_tier_1": ("Incomum", 26), "stack_upgrade_tier_2": ("Raro", 52),
                             "stack_upgrade_tier_3": ("Épico", 63), "stack_upgrade_tier_4": ("Lendário", 79),
                             "advanced_pickup_upgrade": ("Raro", 29)}),
    "flashlight": dict(mod="flashlight", themes=("house",),   # 17 Nov 2026 (was 30/45)
                       items={"flashlight_off": ("Incomum", 10), "headlamp_helmet": ("Raro", 16),
                              "night_vision_goggles_helmet": ("Raro", 16)}),
}

# VANILLA TOOLS in the workshop (user's request, 16 Nov 2026; option A: half the chance in barrels). Chance per
# container (‰) in a chest: Rare = 1.0% (iron pickaxe and flint and steel, 40-65% durability left); Legendary = 0.05%
# (undamaged netherite pickaxe; a new class, 10x rarer than Epic).
TOOLS = dict(iron_pickaxe=dict(p=10, dur=(0.40, 0.65), themes=("workshop",)),
             flint_and_steel=dict(p=10, dur=(0.40, 0.65), themes=("workshop",)),
             netherite_pickaxe=dict(p=0.5, dur=None, themes=("workshop",)))

# JUNK: the mod overrides the 36 AMC tables (same paths) so that NO useful vanilla item is left in the containers.
# Only near-useless items go here: name -> (weight, min, max). The same list in every theme.
JUNK = dict(stick=(12, 1, 6), wheat_seeds=(10, 1, 4), beetroot_seeds=(8, 1, 4), melon_seeds=(8, 1, 4),
            pumpkin_seeds=(8, 1, 4), rotten_flesh=(10, 1, 3), bone=(8, 1, 3), paper=(8, 1, 4), bowl=(6, 1, 2),
            glass_bottle=(6, 1, 2), spider_eye=(4, 1, 1))
# how much junk per container: (chance of having any, in ‰, min, max stacks). No Luck effect (junk is not a prize).
# The _hard tiers have the same junk: the prize of the hard containers comes from the mod.
JUNK_SHAPE = {"chest": (1000, 2, 4), "chest_hard": (1000, 2, 4), "barrel": (300, 1, 2), "barrel_hard": (300, 1, 2),
              "pot": (300, 1, 1), "pot_hard": (300, 1, 1)}

# resolution of the per-item draws: total weight PER_MILLE x ITEM_RES (the chance p, in ‰, can be fractional:
# 0.25‰ = 0.025%)
ITEM_RES = 100
# =====================================================================================================================

# attachments: chance derived from the gun chance (ATT_FRACTION_OF_GUN), in every theme/tier that has guns
for _th in RATES.values():
    for _r in _th.values():
        if "gun" in _r and "att" not in _r:
            _r["att"] = round(_r["gun"] * ATT_FRACTION_OF_GUN)

GUN_LEVEL = {g: (cat, lv) for cat, d in GUN_LEVELS.items() for lv, gs in d.items() for g in gs.split()}
PICK = {"gun": "gun_default", "ammo": "ammo_default", "att": "att"}   # category -> pick table (pick/...)


def load(p):
    """Reads a JSON file relative to the project root."""
    with open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return json.load(f)


TZ = load("docs/tacz_catalog.json")
CONT = load("docs/containers.json")


# ---------------------------------------------------------------- choosing the items
def eligible_guns():
    """Guns that enter the loot: those with a recipe at the gunsmith table of the TACZ default pack."""
    return {g: v for g, v in TZ["guns"].items() if v["craftable"]}


def gun_weights():
    """Weight of each gun (sum ~GUN_WEIGHT_TOTAL): category share x LEVEL_W of its level / sum of its category's
    levels."""
    guns = eligible_guns()
    cat_share = {c: 1.0 / n for c, n in GUN_CAT_ONE_IN.items()}
    tot = sum(cat_share.values())
    cat_share = {c: v / tot for c, v in cat_share.items()}
    for g, v in guns.items():
        assert GUN_LEVEL[g][0] == GUN_TYPE_MERGE.get(v["type"], v["type"]), \
            "level category != TACZ category: " + g
    sums = {c: sum(LEVEL_W[GUN_LEVEL[g][1]] for g in guns if GUN_LEVEL[g][0] == c) for c in cat_share}
    return {g: max(1, round(GUN_WEIGHT_TOTAL * cat_share[GUN_LEVEL[g][0]] * LEVEL_W[GUN_LEVEL[g][1]]
                            / sums[GUN_LEVEL[g][0]]))
            for g in guns}


def ammo_weights():
    """Weight of each caliber by the LEVEL the user gave (docs/ammo_rarity.json), AMMO_LEVEL_W x100.

    Only calibers used by an eligible gun (7.62x25 and 6.8x51 Fury have no gun in the loot and were not rated)."""
    rar = load("docs/ammo_rarity.json")
    ids = [r["id"] for r in rar]
    assert len(ids) == len(set(ids)) and set(ids) == {v["ammo"].split(":")[1] for v in eligible_guns().values()}, \
        "calibers in the file != calibers of the guns: run tools/att_from_nbt.py"
    return {r["id"]: round(AMMO_LEVEL_W[r["level"]] * 100) for r in sorted(rar, key=lambda r: r["id"])}


def ammo_range(c):
    """Min and max rounds per stack: proportional to the max stack, with 9mm as the reference (AMMO_REF)."""
    if c in AMMO_RANGE_OVERRIDE:
        return AMMO_RANGE_OVERRIDE[c]
    ref, lo9, hi9 = AMMO_REF
    base = TZ["ammo"][ref]["stack"]
    st = TZ["ammo"][c]["stack"] or 30
    lo = max(1, int(lo9 * st / base * AMMO_SIZE + 0.5))
    return lo, max(lo, int(hi9 * st / base * AMMO_SIZE + 0.5))


def att_weights():
    """Weight of each attachment by its level (docs/attachments_rarity.json), x100 to fit integers (Mythic 0.5)."""
    rar = load("docs/attachments_rarity.json")
    ids = [r["id"] for r in rar]
    assert len(ids) == len(set(ids)) and set(ids) <= set(TZ["attachments"]), \
        "attachments in the file repeated or missing from the TACZ catalog"
    return {r["id"]: round(ATT_LEVEL_W[r["level"]] * 100) for r in rar}


# ---------------------------------------------------------------- item JSON
def custom(**kw):
    """Loot function that writes `kw` into the minecraft:custom_data component (JSON object)."""
    return {"function": "minecraft:set_components", "components": {"minecraft:custom_data": kw}}


def count(lo, hi):
    """Loot function for the amount: fixed (lo == hi) or drawn between lo and hi."""
    return {"function": "minecraft:set_count",
            "count": lo if lo == hi else {"type": "minecraft:uniform", "min": lo, "max": hi}}


def gun_spawn_ammo(g):
    """Rounds in the magazine the gun spawns with (GunCurrentAmmoCount)."""
    mag = TZ["guns"][g]["mag"]
    if g in GUN_SPAWN_AMMO_EXCLUDED or not mag:
        return 0
    return int(mag * GUN_SPAWN_AMMO_FRACTION + 0.5)


def e_gun(g):
    """Entry for a TACZ gun.

    custom_data as NBT TEXT (SNBT), not a JSON object: Minecraft turns a small JSON number into a BYTE ("5b"), and TACZ
    only reads the magazine if GunCurrentAmmoCount is an INTEGER (GunItemDataAccessor: contains(key, 3)). In SNBT "5" is
    an integer; "0b" is the boolean for the round in the chamber."""
    snbt = '{GunId:"tacz:%s",GunFireMode:"%s",GunCurrentAmmoCount:%d,HasBulletInBarrel:0b}' % (
        g, TZ["guns"][g]["fire_mode"][0], gun_spawn_ammo(g))
    return {"type": "minecraft:item", "name": "tacz:modern_kinetic_gun",
            "functions": [{"function": "minecraft:set_components", "components": {"minecraft:custom_data": snbt}}]}


def e_ammo(c):
    """Entry for a stack of caliber `c`, with the amount from ammo_range."""
    lo, hi = ammo_range(c)
    return {"type": "minecraft:item", "name": "tacz:ammo", "functions": [custom(AmmoId="tacz:" + c), count(lo, hi)]}


def e_att(a):
    """Entry for a TACZ attachment."""
    return {"type": "minecraft:item", "name": "tacz:attachment", "functions": [custom(AttachmentId="tacz:" + a)]}


def e_lr(i, lo, hi):
    """Entry for a LesRaisins consumable (healing or condensed milk)."""
    return {"type": "minecraft:item", "name": "lrtactical:consumable",
            "functions": [custom(ConsumableId="lrtactical:" + i)] + ([count(lo, hi)] if hi > 1 else [])}


def e_fa(i):
    """Entry for a First Aid item, with the amount from FA_COUNT."""
    lo, hi = FA_COUNT[i]
    return {"type": "minecraft:item", "name": "firstaid:" + i, "functions": [count(lo, hi)] if hi > 1 else []}


def e_gear(i):
    """Entry for a grenade/C4 (lrtactical:throwable) or melee weapon (lrtactical:melee)."""
    d = GEAR[i]
    return {"type": "minecraft:item", "name": "lrtactical:" + d["item"],
            "functions": [custom(**{d["key"]: "lrtactical:" + i})] + ([count(d["lo"], d["hi"])] if d["hi"] > 1 else [])}


def e_tool(i):
    """Entry for a vanilla tool; set_damage uses the fraction of durability LEFT (1.0 = undamaged)."""
    d = TOOLS[i]
    e = {"type": "minecraft:item", "name": "minecraft:" + i}
    if d["dur"]:
        e["functions"] = [{"function": "minecraft:set_damage",
                           "damage": {"type": "minecraft:uniform", "min": d["dur"][0], "max": d["dur"][1]}}]
    return e


def e_ammo_box(i):
    """Entry for an empty TACZ ammo box; Level in SNBT so it is an INTEGER."""
    return {"type": "minecraft:item", "name": "tacz:ammo_box",
            "functions": [{"function": "minecraft:set_components",
                           "components": {"minecraft:custom_data": "{Level:%d}" % AMMO_BOX[i]["level"]}}]}


def e_family_item(fam, i):
    """Entry for an item of an optional family (backpack/upgrade or flashlight); backpacks with their slots."""
    e = {"type": "minecraft:item", "name": "%s:%s" % (LEVEL_FAMILIES[fam]["mod"], i)}
    if i in BACKPACK_COMPONENTS:
        up, inv = BACKPACK_COMPONENTS[i]
        e["functions"] = [{"function": "minecraft:set_components",
                           "components": {"sophisticatedcore:number_of_upgrade_slots": up,
                                          "sophisticatedcore:number_of_inventory_slots": inv}}]
    return e


def e_item(kind, i):
    """Entry for an item with its own chance, by the kind returned by item_chances/fa_chances."""
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


# ---------------------------------------------------------------- tables and pools
def table(pools, cond=None):
    """Loot table of type chest; `cond` = NeoForge conditions (e.g. mod_loaded)."""
    t = {"type": "minecraft:chest", "pools": pools}
    if cond:
        t = {"neoforge:conditions": cond, **t}
    return t


def pool(entries, rolls=1, bonus=None):
    """Loot pool; bonus = bonus_rolls (left out when None)."""
    p = {"rolls": rolls, "entries": entries}
    if bonus is not None:
        p["bonus_rolls"] = bonus
    return p


def with_w(e, w):
    """Copy of entry `e` with weight `w`."""
    return {**e, "weight": w}


def pick_tables():
    """Pick tables (what drops when the category is drawn). Name -> (JSON, condition or None)."""
    out = {}
    # the "_default" names are kept for compatibility (from when the police station had its own profile)
    out["pick/gun_default"] = (table([pool([with_w(e_gun(g), w) for g, w in gun_weights().items()])]), None)
    out["pick/ammo_default"] = (table([pool([with_w(e_ammo(c), w) for c, w in ammo_weights().items()],
                                            {"type": "minecraft:uniform",
                                             "min": AMMO_STACKS[0], "max": AMMO_STACKS[1]})]), None)
    out["pick/att"] = (table([pool([with_w(e_att(a), w) for a, w in att_weights().items()])]), None)
    return out


def junk_tables():
    """Overridden AMC tables, junk only. Name 'theme/tier' -> JSON (abandonedmoderncity namespace)."""
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
    """Items with their own chance in this theme/tier: list of (kind, item, p in ‰).

    Pharmacy: healing with fixed values; barrels: x BARREL_ITEM_MULT."""
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
    """First Aid in this theme/tier: list of (item, p in ‰).

    Pharmacy: frozen values (HEAL_PHARMACY_FIXED); elsewhere, chance x HEAL_RARITY_SCALE;
    barrels: x BARREL_ITEM_MULT."""
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
    """[(item, level, item chance in ‰)] for the theme/tier ([] if the family does not apply to the theme)."""
    f = LEVEL_FAMILIES[fam]
    if theme not in f["themes"]:
        return []
    m = f.get("barrel_mult", BARREL_ITEM_MULT) if tier.startswith("barrel") else 1.0
    return [(i, lv, PER_MILLE / n * m) for i, (lv, n) in f["items"].items()]


def chance_pool(entry, p, rolls=1, bonus=None):
    """One independent draw: `entry` with chance p (‰, fractions allowed) or nothing.

    Luck raises the chance through `quality` (LUCK_QUALITY), as in the RATES categories. 100% chance: no `empty`."""
    w = max(1, round(p * ITEM_RES))
    q = max(1, round(w * LUCK_QUALITY))
    ents = [{**entry, "weight": w, "quality": q}]
    if w < PER_MILLE * ITEM_RES:
        ents.append({"type": "minecraft:empty", "weight": PER_MILLE * ITEM_RES - w, "quality": -q})
    return pool(ents, rolls, bonus)


def item_pool(kind, i, p):
    """Independent draw of an item from item_chances/fa_chances (with bonus_rolls 0.0, as it always was)."""
    return chance_pool(e_item(kind, i), p, 1, 0.0)


def family_pool(fam, i, p):
    """Independent draw of an item from an optional family (no bonus_rolls)."""
    return chance_pool(e_family_item(fam, i), p)


def weights(rates):
    """(weight, quality) per category + empty, summing to PER_MILLE at Luck 0 and staying ~PER_MILLE with Luck

    (the empty quality is minus the sum of the others)."""
    res = {}
    for c, w in rates.items():
        res[c] = (w, max(1, round(w * LUCK_QUALITY)))
    res["empty"] = (PER_MILLE - sum(w for w, _ in res.values()), -sum(q for _, q in res.values()))
    return res


def main_tables():
    """For each theme/tier: main table (core), First Aid table and optional family tables. Name -> JSON."""
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
                        continue          # 100% chance: no empty entry (weight 0 is not valid)
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
                continue          # theme without First Aid: no table and no loot modifier
            out["%s/%s_firstaid" % (theme, tier)] = table([item_pool("fa", i, p) for i, p in fa_chances(theme, tier)],
                                                           [{"type": "neoforge:mod_loaded", "modid": "firstaid"}])
    for fam, f in LEVEL_FAMILIES.items():
        for theme in f["themes"]:
            for tier in TIERS:
                pools = [family_pool(fam, i, p) for i, _, p in family_chances(fam, theme, tier)]
                cond = [{"type": "neoforge:mod_loaded", "modid": f["mod"]}]
                out["%s/%s_%s" % (theme, tier, fam)] = table(pools, cond)
    return out


# ---------------------------------------------------------------- expected values (the same math as Minecraft)
def eff(w, q, luck):
    """Effective weight of an entry at Luck `luck` (Minecraft rule: floor(weight + quality*Luck), at least 0)."""
    return max(0, math.floor(w + q * luck))


def item_prob(p, luck):
    """Real chance of a per-item draw (the same math as Minecraft, at the resolution of chance_pool)."""
    w = max(1, round(p * ITEM_RES))
    q = max(1, round(w * LUCK_QUALITY))
    a = eff(w, q, luck)
    e = eff(PER_MILLE * ITEM_RES - w, -q, luck)
    return a / (a + e) if a + e else 0.0


def expected(theme, tier, luck):
    """Expected per container (Luck `luck`): gun, ammo, att in stacks; lr, food, gear, tool, box in draws; fa in
    units."""
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
    for i, p0 in fa_chances(theme, tier):             # First Aid: expected units (chance x mean amount)
        res["fa"] += item_prob(p0, luck) * sum(FA_COUNT[i]) / 2
    for kind, i, p0 in item_chances(theme, tier):     # one draw per item (single roll, no bonus)
        res[kind] += item_prob(p0, luck)
    return res


def preview():
    """Prints the expected loot per structure (docs/containers.json), guns per chest and the chance of a chest having
    anything from the mod."""
    rows = []
    for name, v in CONT.items():
        th = v["theme"]
        if th not in RATES:
            continue
        rows.append((th, name, v))
    rows.sort(key=lambda r: (list(RATES).index(r[0]), -r[2]["total"]))
    print("Expected per structure (one copy): guns | ammo stacks | attachments | LesRaisins healing | "
          "First Aid healing")
    print("Luck 0 in detail; 'guns' also at Luck 1/2/3. Decorated pots get nothing from the mod.\n")
    print("%-14s %-30s %5s | %s | %-23s | %6s %6s" % ("theme", "structure", "cont.", "Luck 0: gun  ammo att  LR   FA",
                                                     "guns L0 L1 L2 L3", "LR L3", "FA L3"))
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
    print("\nChests (chest + chest_hard) per gun, Luck 0 / I / II / III  (1 gun in N chests):")
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
            cells.append("L%d: 1 in %.1f" % (lk, ch / ex))
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
    print("Police station, Luck 0: chance of at least N guns: "
          + "  ".join("N=%d: %.0f%%" % (n, 100 * sum(dist[n:])) for n in (3, 4, 5, 6, 7, 8)))
    print("\nChance of ONE chest having at least 1 item from the mod (TACZ+LesRaisins | + First Aid), by theme and "
          "Luck:")
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
                cells.append("L%d %4.0f%%|%4.0f%%" % (lk, 100 * p_core, 100 * (1 - (1 - p_core) * (1 - p_fa))))
            print("  %-14s %-11s %s" % (th, tier, "   ".join(cells)))


# ---------------------------------------------------------------- writing + checks
def write_json(path, obj):
    """Writes `obj` as indented JSON (2 spaces, UTF-8, trailing newline), creating the folders."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def write(out=OUT):
    """Writes every table and loot modifier into `out` (default: src/main/resources/data) and runs check()."""
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
    print("written: %d tables, %d loot modifiers, %d overridden AMC tables (junk only)"
          % (len(tables), len(glms), len(junk)))


def check(base, gl, tables, glms, junk):
    """Consistency checks of the generated files; exits with an error if anything is wrong."""
    errs = []
    with open(gl, encoding="utf-8") as f:
        listed = json.load(f)["entries"]
    for e in listed:
        if not os.path.exists("%s/loot_modifiers/%s.json" % (base, e.split(":")[1])):
            errs.append("listed GLM does not exist: " + e)
    for n in glms:
        if "%s:%s" % (MOD, n) not in listed:
            errs.append("GLM exists but is not listed: " + n)
    amc_ids = {"%s:chests/%s/%s" % (AMC, th, ti) for th in RATES for ti in TIERS}
    for n, g in glms.items():
        if g["table"].split(":")[1] not in tables:
            errs.append("GLM points to a missing table: " + n)
        if g["conditions"][0]["loot_table_id"] not in amc_ids:
            errs.append("target is not an AMC table: " + n)
    for n, t in tables.items():
        s = json.dumps(t)
        for mid in ["firstaid"] + [f["mod"] for f in LEVEL_FAMILIES.values()]:
            if '"%s:' % mid in s and t.get("neoforge:conditions") != [{"type": "neoforge:mod_loaded", "modid": mid}]:
                errs.append("item from mod %s in a table without the mod_loaded condition: %s" % (mid, n))
        if "pot" in n:
            errs.append("decorated pot table generated: " + n)
        for ref in [x for x in s.split('"') if x.startswith(MOD + ":pick/")]:
            if ref.split(":")[1] not in tables:
                errs.append("missing pick table: " + ref)
    # no vanilla item outside the junk list, in ANY generated table (mod + overridden AMC tables)
    allowed = {"minecraft:" + i for i in JUNK} | {"minecraft:bread"} | {"minecraft:" + i for i in TOOLS}
    for n, t in list(tables.items()) + [("amc:" + k, v) for k, v in junk.items()]:
        for name in re.findall(r'"name": "(minecraft:[a-z_0-9]+)"', json.dumps(t)):
            if name not in allowed:
                errs.append("vanilla item outside the junk list in %s: %s" % (n, name))
    # explicit list (not derived from JUNK_SHAPE): if a tier disappeared from the junk, the AMC's vanilla table would
    # come back without warning
    amc_tiers = ("chest", "chest_hard", "barrel", "barrel_hard", "pot", "pot_hard")
    expect = {"%s/%s" % (th, ti) for th in RATES for ti in amc_tiers}
    if set(junk) != expect:
        errs.append("overridden AMC tables != the 36 AMC tables")
    for g, v in TZ["guns"].items():
        if v["ammo"].split(":")[1] not in TZ["ammo"]:
            errs.append("ammo of gun %s missing from the catalog" % g)
    if errs:
        print("\n".join("ERROR: " + e for e in errs))
        sys.exit(1)


if __name__ == "__main__":
    preview()
    if "--write" in sys.argv:
        write()
