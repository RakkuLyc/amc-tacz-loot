# AMC TACZ Loot — history (13 to 18 Nov 2026)

English translation of the history that lived in `CLAUDE.md` up to 18 Nov 2026 (the Portuguese original is in the git
history: the last version of `CLAUDE.md` before the 18 Nov 2026 translation). Numbers in older sections may have been
replaced by later ones; the current values are in `CLAUDE.md` and in `tools/gen_loot.py`.
Commit hashes were replaced by the commit date and title, because the history of this repository and of the AMC
repository was (or will be) rewritten. "AMC commit" = a commit in the Abandoned Modern City repository.
Versions 1.0.0 to 1.1.2 below are **internal test versions** (private releases); the first public release, made after the
18 Nov 2026 review, is also called 1.0.0 and has the same loot as internal 1.1.2.
Glossary: building = prédio, police station = delegacia, house = casa, workshop = oficina, gas station = posto,
pharmacy = farmácia, hard chest = baú difícil, Luck = Sorte, "1 in N" = "1 a cada N".

## Former "CURRENT STATE" block (version 1.0.1, as written on 17-18 Nov 2026)
(17 Nov 2026: the stage of guns by level, police station 2x, attachments and ammo by level was tested and approved by
the user: "Tested and approved, you can close this stage"; push at the commit of 17 Nov 2026 ".50 BMG: pilha 21-30 e
Lendario de municao de 1/134 para 1/100 baus".)
- **Guns** (17 Nov 2026, reworked; chance per regular chest / hard chest, Luck 0): **building 16.8% / 28.1% (1 in
  5.95 / 3.6 chests), barrels 0.6% / 1.0%** (before 12% / 20% / 0.4% / 0.7%); **police station: 2x the building
  (17 Nov 2026) = 33.6% / 56.2% (1 in 3 / 1.8), barrels 1.2% / 2.0%**, with the same split by category and level as the
  building (the "police" profile was removed). **7 categories** (TACZ's DMR counts as a **rifle**, 26 guns) and
  **5 fixed levels** (Common, Uncommon, Rare, Epic, Legendary): `GUN_CAT_ONE_IN` (building, "1 in N chests": pistol 25,
  smg 29, rifle 42, shotgun 42, machine gun 65, sniper 60, explosive 70; the sum is 16.84%), `GUN_LEVELS` (gun -> level,
  from the user's file "Reformular o sistema de classificação de raridade de armas"; **my choices, approved**: golden
  deagle = Epic, springfield1873 = Uncommon), `LEVEL_W` per GUN (16/8/4/2/1: each level half of the previous one;
  "Option A"). Guns without a level break `gun_weights` (assert). Police station: see the section "Police station 2x"
  at the end (the first version, which kept the old police split, was replaced the same day).
  A gun drops **with 50% of a full magazine** (`GunCurrentAmmoCount` = ammo_amount x 0.5 rounded up: 17 -> 9, magazine
  of 1 -> 1; `HasBulletInBarrel` = false), **except the minigun** (no magazine defined, spawns with 0).
- **Attachments** (REDEFINED on 17 Nov 2026, "Option B, 16/8/4/2/1, include all, the 4 that are not in my files left
  out"): chance of ANY attachment per container = **1.2 x the gun chance** (`ATT_FRACTION_OF_GUN`; "about 20% more
  common than guns"): building chest 20.2%, hard 33.7%, barrels 0.7% / 1.2%; police station (= 2x the building) 40.3% /
  67.4% / 1.4% / 2.4%. Guns and attachments are **independent pools** (`CORE_POOLS`): in the police station hard chest
  the sum goes over 100%. Which one drops: weight by the LEVEL of each of the **109 attachments** of the user's
  classification (color of the concrete ABOVE the chest in their `.nbt` structures; `docs/attachments_rarity.json`,
  made by `tools/att_from_nbt.py <structures folder>`): Common 22 items (light gray, weight 16), Uncommon 3 (lime, 8),
  Rare 14 (light blue, 4), Epic 12 (magenta, 2), Legendary 5 (yellow, 1), **Mythic** 1 (orange, 0.5: only
  `ammo_mod_he`), **Unrated** 52 (chest without concrete: grips, lasers, muzzles, stocks; the Uncommon weight, 8). Items
  per family: sights 40 (with level), extended magazines 17 (no Uncommon; Legendary = ammo_mod_i/hp/slug/fmj), and the
  4 families without level. Included are the 9 listed items that TACZ does not let you craft (4 `oem_stock_*`,
  `stock_psg`, 4 sights `sight_*_rifle`). **Left out** (craftable, not in their files): `ammo_mod_overpressure_recoil`,
  `stock_heavy_spas_12`, `stock_moe`, `stock_tactical_spas_12`. Chance of each item per building chest: Common 0.368%,
  Uncommon/unrated 0.184%, Rare 0.092%, Epic 0.046%, Legendary 0.023%, Mythic 0.012% (police station: double).
- **Barrels** (16 Nov): in the `barrel` and `barrel_hard` tiers the chance of **LesRaisins healing, First Aid, food
  (milk and bread) and grenades/melee weapons is HALF the chest chance**, in every theme (pharmacy included). Guns,
  ammo and attachments have their own reduction in barrels (RATES: 3% to 25% of the chest chance). Junk in barrels:
  30% with 1-2 stacks. `BARREL_ITEM_MULT = 0.5`.
- **Ammo** (own pool; 17 Nov 2026): **police station = the same chances as the building**: chest 52%, hard 86.6%,
  barrels 6.2% / 11.4% (before the police change: 80 / 100 / 20 / 36%). Workshop unchanged (4 / 7 / 1.5 / 3%), but it
  uses the same caliber mix. **Caliber by LEVEL** (user, `tacz_ammo.nbt` -> `docs/ammo_rarity.json`, via
  `tools/att_from_nbt.py`; `AMMO_LEVEL_W` 16/8/4/2/1 per caliber): Common 9mm, .45 ACP, .22 WMR, 4.6x30; Uncommon
  7.62x39, 5.56, 7.92x57, 12g; Rare 5.7x28, 5.8x42, 5.45, 7.62x54, .338, .45-70, .357; Epic .300 BLK, .308, .500,
  .30-06, .50 AE, 40mm, RPG rocket; Legendary .50 BMG (**weight 1.35, stack 21-30**, adjusted on 17 Nov). Share of the
  stacks: Common 11.5% each, Uncommon 5.8%, Rare 2.9%, Epic 1.4%, Legendary 0.97%. Chance per building chest of >= 1
  stack: Common 11.1%, Uncommon 5.8%, Rare 2.9%, Epic 1.5%, .50 BMG 1.0% (1 in 100; was 0.74% / 1 in 134). 1 to 3
  stacks, full size (9mm 24-50). Rounds per hit ~65.6.
  **Each ammo hit gives 1 to 3 stacks of drawn calibers** (the same caliber can repeat), with rounds per stack
  proportional to the max stack, **at the original size** (9mm 24–50 with stack 60; 12g 14–30; .308 19–40; 22wmr
  26–53; 40mm and rocket 2–5). `AMMO_STACKS = (1, 3)`, `AMMO_SIZE = 1.0`.
  **Total rounds per building chest ~31 (double the 1-stack version); police station ~48.**
- **LesRaisins healing** (chance of EACH item per container, independent; the same in every theme except the pharmacy;
  "rarity doubled" on 16 Nov = chances x0.5): Common vaseline, ibuprofen, amoxicillin, golden star **4.6% each**;
  Uncommon blood pack **2.3%**, CAR **2.1%**; **Rare** AI-2 and CMS **1.0%**; **Epic** SURV12 **0.5%**.
  **Pharmacy = values frozen "as it was"** (`HEAL_PHARMACY_FIXED`): Common 9.2%, blood pack 9.0%, CAR 8.5%, AI-2 8.0%,
  CMS 7.0%, SURV12 4.0%.
- **Food** (17 Nov 2026): condensed milk **4%** per chest (1–3 units), only in buildings and houses; bread **16%** per
  chest (**1–5**), only in houses. Half in barrels (milk 2%, bread 8%). Before: milk 8%, bread 20% with 4–12.
- **LesRaisins equipment** (chance of EACH item per container, independent; every theme **except the pharmacy**; **in
  the police station the throwable chances double**): M67 Grenade 9.2% (**3 to 5**; police 18.4%), RGN Grenade 4.1%
  (**2 to 4**; police 8.2%), C4 Sticky Bomb 3.0% (1; police 6.0%), Dagger / Karambit / Baseball Bat 2.0% each (1, full
  durability). Items: `lrtactical:throwable` (`ThrowableId`) and `lrtactical:melee` (`MeleeWeaponId`). The detonator is
  **not** in the loot (the C4 gives it when thrown, confirmed by the user). smoke/flash/molotov/flash shield left out.
  (Later on 18 Nov 2026: throwables only in building and police station; baseball bat 1.5%.)
- **First Aid** (optional, its own table with `neoforge:mod_loaded`; chance of EACH item per container, independent,
  the same in every theme except the pharmacy; x0.5 on 16 Nov): plaster **7.5%** (4–14 units, "Very common");
  bandage, adrenaline injector, painkillers **4.6%** (Common; bandage 2–10); defibrillator **2.1%** (Uncommon);
  **Rare** morphine **1.0%**; **Epic** morphine injector **0.5%**. **Pharmacy frozen**: plaster 15%, Common 9.2%,
  morphine 8.2%, defibrillator 8.2%, injector 4.0%. `FA_CHANCE`, `FA_CLASS`, `FA_COUNT`.
  Classes (most common -> rarest): Very common, Common, Uncommon, Rare, **Epic** (new, 16 Nov). Rare = base 4.0% and
  Epic = 2.0% LR (and 2.0% / 1.0% FA) before x0.5: my values.
- **Vanilla junk** (stick, 4 seeds, rotten flesh, bone, paper, bowl, bottle, spider eye) in the 36 overridden AMC
  tables; no useful vanilla items (only exception: bread).
- **AMC with drawn chests** (16 Nov 2026): the table names did not change (6 themes x chest/barrel/pot x _hard), so
  the mod needed no change. The 10 `building_*` buildings lost the template chests and gained chests drawn per copy
  (small 12–28, large 38–65, plus 30% of the barrels become chests); the ramp and the police station did not change.
  `docs/containers.json` was measured again (mean of 6 copies). Spawning now uses categories by height
  (`building_small`, `building_large`...): `measure_containers.py` adjusted.
  **18 Nov 2026: measured again with AMC 1.0.0** (one copy for the 40 structures without drawn chests; mean of 5-6
  copies for the 12 with drawn chests): the 3 `workshop_medium_*` went from 1 to 4 chests (AMC commit of 2026-11-17
  "Medium workshop: 3 chests added to its .nbt (work bay, back room, terrace)"); in the buildings the means varied
  within the noise of 6 copies. Only the preview changes.
- **No healing items** (LesRaisins and First Aid) in the **workshop, gas station and police station** (16 Nov,
  `HEAL_EXCLUDED_THEMES`; those themes have no `_firstaid` table). Milk stays.
- **Condensed milk: 1 to 3 units** per hit (before 2 to 4), **only in buildings (`building`) and houses** (16 Nov; not
  in the pharmacy, police station, workshop or gas station).
- **Vanilla tools only in the workshop** (16 Nov, `TOOLS`, option A = half in barrels): iron pickaxe and flint and
  steel **Rare** (chest 1.0% / barrel 0.5%, 40–65% durability left); netherite pickaxe **Legendary** (new class, 10x
  rarer than Epic: chest 0.05% / barrel 0.025%, undamaged). Allowed vanilla exceptions: bread and these 3 tools.
  Resolution of the per-item draws: `ITEM_RES = 100` (1 in 100,000).
- **Decorated pots** get nothing from the mod. Themes: building, police_station, pharmacy, house, workshop,
  gas_station (the AMC removed `building_large`).
- **Tools**: `gen_loot.py` (preview / `--write`), `sample_items.py` (chance per item on a test server), `rcon.py` and
  `rconlib.py` (RCON), `measure_containers.py`, `tacz_catalog.py`, `lr_catalog.py`, `att_from_nbt.py`; tests in
  `tests/` (`python3 -m unittest -v`). `sample_loot.py` was removed (18 Nov 2026).

## User's decisions (13 Nov 2026)
- Only the TACZ default pack (70 guns); Gunpowder Revolution (`hamster`) is left out for now.
- Guns/ammo/attachments in `building` (the `building_large` theme was removed from the AMC on 14 Nov 2026, AMC commit
  of 2026-11-14 "Loot theme building_large taken out: every building uses building"); **the police station gets more
  guns**: the AMC gained the `police_station` theme (AMC commit of 2026-11-13 "Loot theme police_station: its own
  tables (same vanilla items as building)...").
- Healing: plenty in the pharmacy; a little in houses, workshops and gas stations; workshops also with a little ammo.
- **Decorated pots (`pot`) get nothing** (see the facts).
- **No useful vanilla items (14 Nov 2026):** the mod's tables never had vanilla items; the vanilla items in the
  containers came from the AMC's own tables (94 kinds). The mod now **overrides the AMC tables** (same paths,
  `data/abandonedmoderncity/loot_table/chests/`) with **junk** only, the same list in every theme: stick,
  wheat/beetroot/melon/pumpkin seeds, rotten_flesh, bone, paper, bowl, glass_bottle, spider_eye. Amount (`JUNK_SHAPE`
  block of the generator): chest 2–4 stacks, barrel/pot 30% of having 1–2 (pot 1); `_hard` tiers equal (the prize comes
  from the mod). No Luck effect. The user's choice between changing the AMC, overriding from the mod, or leaving it.
  (Written then as "42 tables"; the correct number is 36: 6 themes x 6 tiers.)
- TACZ, LesRaisins and AMC are required; **only First Aid is optional** (`neoforge:mod_loaded`). (Later: Sophisticated
  Backpacks and TCT Flashlight are optional too.)
- Generous loot, but not abundant. Every table with `weight`, `quality` and `rolls`/`bonus_rolls` so Luck works.
- Repository: same name (`RakkuLyc/amc-tacz-loot`), new and empty (the old one deleted and recreated on 14 Nov 2026).

## Verified facts (in the jars/log, not from memory)
- Injection: native GLM `neoforge:add_table` + condition `neoforge:loot_table_id` (field `loot_table_id`); registered
  in `data/neoforge/loot_modifiers/global_loot_modifiers.json` (`replace:false`). Works (test of 13 Nov 2026).
- TACZ: generic items `tacz:modern_kinetic_gun` / `tacz:ammo` / `tacz:attachment`; the ID lives in
  `minecraft:custom_data` (`GunId`, `AmmoId`, `AttachmentId`, values `tacz:<id>`). When creating a gun, TACZ itself
  (`GunItemBuilder`) writes `GunId`, `GunFireMode` (enum name in capitals: `SEMI`/`AUTO`/`BURST`),
  `GunCurrentAmmoCount`, `HasBulletInBarrel` and `HeatAmount`. Catalog (70 guns with type, ammo and fire modes;
  25 ammo types; 128 attachments) in `docs/tacz_catalog.json`, made by `tools/tacz_catalog.py`.
  Eligible items = those with a recipe at the gunsmith table of the default pack (`craftable` in the catalog: 70 guns,
  25 ammo types, 104 of 128 attachments; left out are `oem_*`, `*_default` and built-in variants). An objective
  criterion, not by name. The jar's data JSON files have `/* */` comments (the catalog parser handles them); `minigun`
  has no `ammo_amount`.
  **Verified by the user in game (13 Nov 2026):** a gun with only `GunId`+`GunFireMode` fires, and the
  ammo/attachment/healing work.
  **Not verified:** the generated guns now also carry `GunCurrentAmmoCount: 0` and `HasBulletInBarrel: false`;
  reloading with the ammo that comes with them is still to be tested.
- LesRaisins: healing items are `lrtactical:consumable` with `custom_data.ConsumableId = "lrtactical:<id>"`.
  Healing > 0 (`docs/lr_catalog.json`): `ai2`, `amoxycillin`, `blood_pack`, `carfak`, `cms`, `goldenstar`,
  `ibuprofen`, `surv12`, `vaseline`; `condensed_milk` only gives food (out of the healing loot). Those with durability
  (`max_durability` > 0) come 1 at a time.
- First Aid: normal items `firstaid:` `plaster`, `bandage`, `painkillers`, `morphine`, `morphine_injector`,
  `adrenaline_injector`, `defibrillator`.
- Item from an optional mod: the **table** and the **GLM** that mention it need
  `"neoforge:conditions":[{"type":"neoforge:mod_loaded","modid":"firstaid"}]`; without First Aid the server starts
  normally (tested).
- Luck (Minecraft 1.21.1 bytecode): effective weight = `floor(weight + quality*Luck)`; rolls =
  `rolls + floor(bonus_rolls*Luck)`. `bonus_rolls` < 1 does nothing at Luck I; `quality` is the lever that already
  responds at Luck I. The AMC uses `setLootTable(key, seed)` (lazy loading: it reads `player.getLuck()` when chests and
  barrels are opened). `random_chance` ignores Luck: do not use it to decide whether there is loot; use
  `minecraft:empty` with a negative `quality`. The console `/loot` **does not apply Luck** (`LootCommand` does not use
  it): RCON tests are always at Luck 0; Luck > 0 only by calculation and in game (`/effect give @s minecraft:luck`).
- **Decorated pots**: `DecoratedPotBlockEntity.getTheItem()` calls `unpackLootTable(null)` (no player, **no Luck**), and
  when the table produces more items than slots Minecraft logs `"Tried to over-fill a container"`. (Written then as
  "fills nothing / would also empty the AMC item"; CORRECTED on 18 Nov 2026 from the source of `LootTable.fill`: it
  fills until the slots run out and the excess, picked at random, is lost; a pot would keep 1 random item.) That is why
  the mod does not inject into pots.
- A nested `minecraft:loot_table` entry with `value` = table id or inline table works (tested; it is how a gun came
  with its ammo). Composite entries (group etc.) have no weight.
- The police station (63 containers) has its own `police_station` theme in the AMC (same vanilla tables as
  `building`). Containers per structure and kind measured in game: `docs/containers.json`
  (`tools/measure_containers.py`; matches the AMC total).

## Numbers approved by the user (13 Nov 2026, "I approve")
- (The totals per structure approved on 13 Nov were replaced by the change of 14 Nov, below; rarities and Luck stay.)
- Gun rarity by type (weight): default pistol 10, smg 6, shotgun 6, rifle 4, dmr 2, sniper 1.5, mg 1, rpg 0.3; police
  station pistol 8, smg 8, shotgun 8, rifle 6, dmr 2.5, sniper 1.5, mg 1, rpg 0.3 (rpg7, m320 and minigun included, very
  rare; ammo .50 BMG, 40mm and rocket x0.15–0.4). The gun comes **unloaded** and **without** ammo with it (changed on
  14 Nov, below).
- Healing: common items (ibuprofen, blood_pack, vaseline; plaster, bandage) drop more than the rare ones (ai2, carfak;
  defibrillator).
- Luck: `quality` = 25% of the base chance per level (x1.25 / x1.5 / x1.75 at Luck I/II/III); `bonus_rolls` only on hard
  chests (0.34: Luck III) and regular chests (0.2: Luck V). Police station 5.7 -> 7.1 -> 8.3 -> 11.9 guns.
- All these values (junk included) are in the top block of `tools/gen_loot.py`; changing a number = editing the line,
  `--write`, build.

## How to test (as written up to 18 Nov 2026)
- **Real Luck only in game, opening real containers** (neither `/loot` nor the console apply Luck): `/amcs spawn
  police_station abandoned_police_station` twice, far apart; open the chests of one without the effect and those of the
  other with `/effect give @s minecraft:luck infinite 2`; compare with the preview (big noise in a single structure:
  look for a clear difference).
- Chunks generated before an AMC change keep the old table ids (the id is saved when the container is placed);
  containers already opened have no table anymore. Test in a new world or with `/amcs spawn`.
- The mod requires AMC 1.0.0 or newer (18 Nov 2026; before `[0.1.0,)`, which accepted old builds without the
  `police_station` theme). The test server uses the jar from `../AbandonedModernCity/build/libs/abandonedmoderncity-1.0.0.jar`.
- Build: `JAVA_HOME=/usr/lib/jvm/java-21-openjdk ./gradlew build -Dorg.gradle.java.installations.paths=$JAVA_HOME`
  (the system's default Java is 27, too new for Gradle).
- Automated tests and the sampler: see `CLAUDE.md`.
- Test server: copy into `run/mods/` the jars from `../AbandonedModernCity/libs` (TACZ, First Aid, LesRaisins) and the
  AMC jar; `run/server.properties` with RCON (port 25575, password `teste`; another password: environment variable
  `AMC_RCON_PASSWORD`); `./gradlew runServer` (same options);
  `python3 -I tools/rcon.py "setblock 0 100 0 minecraft:chest" "loot insert 0 100 0 loot <table>" "data get block 0 100 0 Items"`;
  `... tools/rcon.py stop`. (`run/` is not versioned.)

## Generator (`tools/gen_loot.py`)
- `python3 -I tools/gen_loot.py` prints the **preview** (expected per structure, Luck 0 to 3; chance of a chest having
  something from the mod); `--write` deletes and rewrites `src/main/resources/data/amctaczloot` and
  `global_loot_modifiers.json` and runs the consistency checks. **All numbers live in the top block of the script**
  (chances in ‰ per theme/tier, Luck, gun rarity).
- Generated structure: `<theme>/<tier>_core.json` (2 independent pools: gun/attachment/LesRaisins healing and ammo;
  TACZ+LesRaisins) and `<theme>/<tier>_firstaid.json` (First Aid healing, with `neoforge:mod_loaded`); pick tables in
  `pick/`; one GLM `neoforge:add_table` per table, filtered by `neoforge:loot_table_id`. Themes: building,
  police_station, pharmacy, house, workshop, gas_station; tiers chest, chest_hard, barrel, barrel_hard (no pot).
- Validation (13 Nov 2026): a real server with AMC+TACZ+LesRaisins+First Aid, `tools/sample_loot.py <theme> <tier> [N]`
  sampled hundreds of chests: the observed means match the preview (Luck 0). Data: `tools/tacz_catalog.py`,
  `tools/lr_catalog.py`.
- Overriding the AMC tables: `mods.toml` declares `ordering="AFTER"` for the AMC (the mod loads later, so its files with
  the same path win). **Tested (14 Nov 2026):** with the original AMC jar (old vanilla tables) in the `mods` folder,
  1,680 samples of chests/barrels from the 7 themes gave only junk + mod items. **Not tested:** without the `ordering`
  (I do not know whether it is needed) and the pots (files generated, not sampled). Load order between mods is not a
  Minecraft guarantee: if another mod also overrides these tables, the result depends on load order. The generator's
  checks fail if any vanilla item outside the junk list appears.

## Change of 14 Nov 2026 (user's request): more guns, and the AMC changed
- The AMC removed `building_large` (AMC commit of 2026-11-14 "Loot theme building_large taken out: every building uses
  building"), removed 70% of the buildings' barrels and turned the rest into chests (AMC commit of 2026-11-14 "Barrels of
  the buildings: 70% taken out, the others chests, copy by copy") and created hard containers in
  basements/terraces/attics (AMC commit of 2026-11-14 "Hard containers also underground, on the terrace and in the
  attics of the houses"). **`docs/containers.json` was measured again** with the current AMC (the crash building went
  from 201 to 94 containers; buildings are almost all chests; the ramp still has 242 barrels).
- Request: buildings **1 gun in 3–7 chests**; police station **1 gun in 3–4 chests "guaranteed"**.
  Implemented (Luck 0, per chest; barrels stay rare): `building` chest 200‰ (1 in 5), hard chest 333‰ (1 in 3);
  `police_station` chest 250‰ (1 in 4), hard chest 333‰ (1 in 3). Result: buildings 1 gun in **5.0** chests, police
  station in **3.6**. Sampling on the server: building chest 0.191 (exp. 0.200), hard 0.332 (0.333); police station
  0.259 (0.250), hard 0.323 (0.333).
- "Guaranteed": a loot table is an independent draw per container; **there is no exact guarantee per structure** in a
  data-only mod. The closest is probability: in the police station (Luck 0) the chance of at least 4 guns is 99%, 5:
  98%, 6: 94%, 8: 76%.
- Consequence (to watch): the total per building rose a lot (brutalist ~46 guns, ramp ~33, tower ~14, apartments ~2),
  because buildings have hundreds of chests. If it is too much, lower `gun` in `RATES["building"]` (1 in 7 = 143‰).

## Ammo (option B, chosen by the user on 14 Nov 2026)
- Request: ammo **no longer** comes with the gun; it is random, with rarity per caliber according to the guns that use
  it. Implemented: the core table has **2 independent pools** (gun/attachment/LR healing; and ammo). `pick/gun_*` now
  only has guns.
- Caliber: weight = sum of the rarities (by gun type) of the guns that use the caliber, with an extra reduction for
  .50 BMG/.338/.45-70/.500 mag (x0.4–0.5) and 40mm/rocket (x0.15) — `ammo_weights()`. Most common: 12g ~20%, 9mm ~18%,
  .45 ACP ~15% (building).
- Amount = **the same total ammo as before** (loose + what came with the gun): building chest 26%, hard 43.3%; police
  station 40% / 58.3%; building barrels 3.1% / 5.7%, police station barrels 10% / 18%; workshop unchanged (4% / 7%,
  barrel 1.5% / 3%). Stack: from 1/6 to 1/2 of the caliber's full stack (e.g. 9mm 10–30 rounds). Luck: `quality` like
  the other categories.
- Validated on the server (3,000 building chests): 0.270 stacks/chest (exp. 0.260); calibers match the expected share;
  of the chests with a gun only 26% have any ammo (= the overall chance) and only 3% the gun's caliber (before 100%).
- Reference: the ammo of Apocalypse Loot (Lost Cities) is ~8–14x larger per chest and has a rarity range of 14:1 (ours
  is ~270:1); the user chose to keep our option B. Simulation of 20 chests in `run/tmp/simulate_ammo.py` (not versioned).

## Proposal C applied (15 Nov 2026) — replaces the ammo rarity/amount and the building gun rates
- User feedback (screenshot of the green tower: 14 guns, ~10 visible stacks): guns ok, little ammo. The inventory
  **merges equal stacks**, so the stack count on screen is misleading (9mm 55 > max 50 of one stack).
- **Equal ammo rarity** for every caliber that has a gun (23; `7.62x25` and `6.8x51 Fury` have no gun and stay out).
  **Amount per stack** proportional to the max stack, 9mm as reference 24–50 (`AMMO_REF`): stack 60 → 24–50; 64 →
  26–53; 50 → 20–42; 48 → 19–40; 42 → 17–35; 36 → 14–30; 30 → 12–25; 6 (40mm, rocket) → 2–5. A single table
  `pick/ammo` (no gun profile).
- **Building guns −40%** (regular chest 12% = 1 in 8.3; hard 20% = 1 in 5; barrels 0.4% / 0.7%). **Police station guns
  unchanged** (25% / 33.3%, barrels 3% / 6%). **Ammo x2** in building and police station: building chest 52%, hard
  86.6%, barrels 6.2% / 11.4%; police station chest 80%, **hard 100% (cap, no `empty` entry: weight 0 is not valid)**,
  barrels 20% / 36%. Workshop and other themes unchanged.
- Assumed interpretation: "keep the amount of useful rounds as it is" = keep the defined stack sizes; the −40% / x2
  factors were my proposal (approved). Before: green tower 18.1 guns / 408 rounds / 16.7 useful per gun; now (expected)
  10.9 guns / 47.3 stacks / ~1,350 rounds / ~40 useful per gun; police station 9.4 guns, 33.3 stacks.
- Validated on the server (Luck 0): guns and ammo per chest match (building 0.120 and 0.542; police station 0.244 and
  0.811; hard 1.000); 23 calibers, shares 3.6–5.0% (expected 4.35%); rounds per stack inside the ranges above. The
  section "Ammo (option B)" above was superseded on this point.

## Mixed caliber, option 2 (15 Nov 2026) — replaces "equal rarity" of proposal C
- Feedback (crash building, ~66 chests, 3 guns, ~33 stacks): ammo as designed (34.3 expected), but **3 guns** (chance
  of ≤3: 3.6%) and, with all calibers equal, only ~24% of the ammo fits the guns found (few guns cover few of the 23
  calibers). Before, I had shown only the mean of "useful rounds per gun"; **the variation is large and must be shown**.
- User's decision (option 2): the chance of each caliber is **half equal for all and half by the popularity of the
  guns** that use it (`AMMO_MIX_UNIFORM = 0.5`; popularity = sum of the type weight of the theme's guns). Tables
  `pick/ammo_default` and `pick/ammo_police` (the police station uses its own gun weights). Most common (building): 12g
  11.9%, 9mm 10.8%, .45 ACP 9.3%, 5.56 5.9%; rarest ~2.4% (40mm, rocket, .45-70, 7.92x57). Gun/ammo rates and stack
  sizes of proposal C **unchanged**.
- Validated on the server: 100 rounds of 66 chests (crash building): 7.5 guns, 34.8 stacks, ~416 useful rounds, median
  58 useful/gun (before 33), 38% of the ammo fits (before 24%), 3% of the rounds with <20 useful/gun (before 16%).
  Calibers match the expected (12g in buildings came out at 14.6% against 11.9% — ~3σ, file weights checked; in the
  police station it came out below; treated as noise).

## LesRaisins healing and food (15 Nov 2026) — replaces the previous healing weights/shares
- **Chance of each item PER CONTAINER, independent of the others** (not a share): vaseline 19.5%, ibuprofen 19%,
  amoxicillin 18%, golden star 17% (Common); blood pack 9%, CAR 8.5%, AI-2 8%, CMS 7% (Uncommon); SURV12 **4%** (Rare;
  the user asked for 3% and then to "lower the rarity a little" — interpreted as a little more common). Sum 110% = ~1
  LesRaisins healing item per container (before ~4%).
  The same chance in every theme and container type; `HEAL_LR`, `HEAL_CLASS`, `PHARMACY_MULT` in the top block of
  `gen_loot.py`.
- **Pharmacy**: multiplier **x2 only on Uncommon and Rare** (blood pack 18%, CAR 17%, AI-2 16%, CMS 14%, SURV12 8%);
  Common unchanged. The x2 is my choice (the user asked for a multiplier without a value).
- **Food**: condensed milk 8% per container, 2–4 units, in every theme (pharmacy included: my assumption); **bread
  (vanilla, an explicit exception from the user) 20%, 4–12 units, only in houses**. The milk already restores 6 hunger,
  saturation 1.6 and applies the Saturation effect (2 s) in the LesRaisins item itself (checked in the JSON). First Aid
  unchanged (still per category, `fa`).
- Implementation: each item has its own pool (item with `weight` = chance in ‰ and `quality` = 25% per Luck level;
  `empty` entry with the rest); the `pick/lr` table no longer exists. The generator's check now accepts
  `minecraft:bread` besides the junk.
- Validated on the server (Luck 0): building (2,500 chests) vaseline 20.2%, SURV12 3.6%, milk 7.0% (2–4); house
  (2,000) bread 20.1% (4–12, mean 7.9); pharmacy (2,000) Uncommon 13–18%, SURV12 7.3%; workshop barrel and police
  station hard chest with the same chances as the building; no bread in buildings.
- Monte Carlo (Luck 0): green tower ~100 LR healing items (Common 67 / Uncommon 30 / SURV12 3.6), 7.3 stacks of milk;
  ramp 439; house 63 healing items and ~91 units of bread; large pharmacy 33.6. **Scale ~27x the previous one (3.6
  healing items in the green tower)**; risk of overflowing a container only in dispensers/droppers (9 slots): ~1 in
  125,000–250,000 containers (written then: "the container stays empty if it overflows"; corrected on 18 Nov 2026: the
  excess is lost).

## Option C: LesRaisins healing x0.5 (15 Nov 2026)
- Feedback: a large pharmacy gave ~34 healing items (expected ~41 with LR+First Aid+milk; it was not bad luck). User's
  choice: **everything x0.5** on the LesRaisins healing chances (`HEAL_SCALE = 0.5`, applied on top of the pharmacy
  multiplier; rounded in ‰).
- Chances per container now: vaseline 9.8%, ibuprofen 9.5%, amoxicillin 9.0%, golden star 8.5% (Common); blood pack
  4.5%, CAR 4.3%, AI-2 4.0%, CMS 3.5% (Uncommon); SURV12 2.0% (Rare). Sum 0.55 per container. **Pharmacy**: Uncommon
  and Rare with the old x2, so they go back to the values before x0.5: blood pack 9.0%, CAR 8.5%, AI-2 8.0%, CMS 7.0%,
  SURV12 4.0%; Common as elsewhere (sum 0.733). Milk 8%, bread 20% (houses only) and First Aid **unchanged**.
- Validated on the server: building (3,000 chests) vaseline 9.7%, SURV12 1.9%; pharmacy (2,500) Uncommon 6.8–9.1%,
  SURV12 4.4%; house bread 20.6%.
- Monte Carlo (Luck 0), LesRaisins healing items: green tower 50 (39–62); brutalist 126; ramp 220; police station 35;
  house 31; workshop 34; gas station 17; large pharmacy 16.9 (11–24); small pharmacy 12.4 (7–18). Before the change of
  15 Nov they were 3.6 in the green tower and 3.6 in the large pharmacy.

## LesRaisins Common items with the same chance (15 Nov 2026)
- Request: "all LesRaisins common items with the same weight". The 4 Common items (vaseline, ibuprofen, amoxicillin,
  golden star) now have 184‰ (18.4%) before x0.5 = **9.2% per container** (mean of the old 19.5/19/18/17; total of the
  Common items unchanged at 36.8%). Uncommon, Rare, pharmacy, milk, bread and First Aid unchanged. The value 18.4% was
  chosen by me (the user gave no number).
- Validated on the server (Luck 0): building (4,000 chests) Common 8.8–9.9%; pharmacy (3,000) 9.2–10.5%. Lesson:
  **always send `tools/rcon.py stop` at the end of a test**; a forgotten server makes the next one fail with "FAILED TO
  BIND TO PORT" and the sampler measures the old server without warning (it happened once; the test was redone). To see
  whether a server is open use `pgrep -f '[b]ootstraplauncher'` (a plain `pgrep` counts the command itself).

## Ammo in 1 to 3 stacks of different calibers (option C, 15 Nov 2026)
- Finding: in a **real** chest Minecraft already splits each stack into several pieces spread over random slots
  (`shuffleAndSplitItems`, only when there are free slots); the `/loot insert` of the tests does NOT. Before the change
  a chest with ammo had **1 caliber only in ~5 pieces** (~6 rounds each). So "loose rounds spread around" already
  existed; what was missing was more than one caliber per chest.
- Apocalypse Loot (reference): its own ammo pool, each roll = 1 stack of a caliber by weight, 1–3 rolls (2–5 in the
  richest tables), `bonus_rolls` 1.0, calibers can repeat, large stacks (9mm 21–57), no small-stack trick (relies on
  Minecraft's split).
- User's choice: **option C** = the chance of the container having ammo did not change (building chest 52% etc.), but
  each hit draws calibers from `pick/ammo_*` with uniform `rolls` **1 to 3** (first 2–3, then the user asked for 1–3),
  stacks at **50%** of the size to keep the total rounds (2.0 stacks x 0.5 = 1; with 2–3 stacks it would be 0.4). The
  50% was my choice (keep the total); if the user preferred 40% the total would drop ~20%.
- Validated in a real chest (real filling forced with `execute if items`, 800 building chests): 54% with ammo;
  different calibers per chest with ammo: 1 (37%), 2 (34%), 3 (29%), mean 1.9; ~8 pieces per chest; 16.4 rounds per
  chest (expected 15.7). Police station (500): 80% with ammo, 22.9 rounds (expected 24.0). Risk of a 9-slot container
  overflowing (dispenser/dropper): 1 in 77,000 to 500,000.
- To test the real filling: `setblock ... chest{LootTable:"...",LootTableSeed:1L}` + `execute if items block ...
  container.0 minecraft:stone` + `data get block ... Items`. **The user's Minecraft in Prism Launcher shows up as
  `bootstraplauncher` in `pgrep`: never kill it; to know whether the test server is open, use port 25575 (`ss -ltn`).**

## Stack size back to the original (15 Nov 2026)
- Request: "the stack size must be equal to the previous value, unchanged" → `AMMO_SIZE = 1.0` (9mm 24–50 etc.), with
  1 to 3 stacks per hit.
- **Consequence (the user was warned):** the total rounds per container doubled (mean 2.0 stacks x full size):
  building chest 15.6 → ~31, police station ~24 → ~48; green tower ~2,800 rounds (before ~1,400). To go back to the old
  total it would be enough to lower the ammo chance in `RATES` x0.5 (not applied).
- Validated: observed sizes equal to the expected ones (9mm 24–50, 308 19–40, 22wmr 26–53, 338 12–25, 40mm 2–5; 12g
  reached 36 by merging two stacks in `/loot insert`, full stack = 36); real chest (800 building chests): 54% with
  ammo, calibers 1/2/3 = 37/34/29%, 33.0 rounds per chest (expected 31.2); police station (500): 80%, 46.4 rounds
  (expected 47.9).

## First Aid per item and large amounts (16 Nov 2026)
- Classes asked by the user: Very common = plaster; Common (same category as LesRaisins) = bandage, adrenaline
  injector, painkillers; Uncommon = morphine, defibrillator; Rare = morphine injector. Then: "increase the stack amount
  drastically": plaster **4–14**, bandage **2–10** (max stack of both in First Aid = 16, `stacksTo(16)` in the
  registry; the defibrillator has durability). The user did not approve/adjust the chance numbers I proposed; applied
  anyway.
- The old system (rate per category `fa` + `pick/fa` with weights) was removed: First Aid is now one pool per item
  (like the LR healing). `fa` left `RATES`.
- Validated (Luck 0): building (3,000 chests) plaster 13.5% (4–14), bandage 8.9% (2–10), Common ~9%; pharmacy Uncommon
  7.4–9.0%, injector 3.6%; workshop barrel equal to the building; **without the First Aid jar the server starts without
  errors, with no `firstaid:` items and the rest of the mod normal**.
- Monte Carlo (First Aid units): green tower ~199 (plaster 123, bandage 50), ramp ~872, house ~125, police station
  ~138, large pharmacy ~52, small ~39. **Scale ~38x the previous one (5 in the green tower).** Risk of overflowing a
  dispenser/dropper (9 slots): ~1 in 5,000 (police station hard barrel), 1 in 12,000 (police station barrel), 1 in
  38,000 (building barrel); (written then: "the container stays empty"; corrected on 18 Nov 2026: the excess is lost).

## LesRaisins grenades, C4 and melee weapons (16 Nov 2026)
- User's classification: Common = M67; Uncommon = RGN; in-between (between uncommon and rare) = C4; Rare = Dagger,
  Karambit, Baseball Bat. Final request: "base it on the LesRaisins healing chance values", M67 "always 3 to 5" and RGN
  "at least 2, at most 4". Values: M67 9.2% (= healing Common), RGN 4.1% (mean of the healing Uncommon items), C4 3.0%
  (midpoint uncommon-rare, my choice), Rare 2.0% (= SURV12). Config: `GEAR`, `GEAR_EXCLUDED_THEMES`.
- Grenade max stack = 3 (`stack_size` in the item JSON): the excess of a draw of 5 becomes another stack (loot stack
  splitter). In a real chest the units appear in pieces of 1–2 spread over the slots (total per chest stays 3–5 / 2–4).
- Sampling patterns fixed: `sample_items.py` now recognizes `ThrowableId` and `MeleeWeaponId`. Lesson: **a regex with
  a specific id + `.*?` with `re.S` picks the count of the wrong item**; match the generic item `\{count: N, Slot: Xb,
  ... id: "..."\}` and only then filter.
- Validated (building, 4,000 chests): M67 8.7% (3–5), RGN 4.6% (2–4), C4 3.0%, melee weapons 1.8–2.2%; pharmacy 0
  items; 0 load errors.
- Monte Carlo (Luck 0): 100 chests ≈ 37 M67 (18–57), 12 RGN, 3 C4, 2 of each melee weapon (65% chance of getting all
  3); green tower ≈ 34 M67, 11 RGN, 2.7 C4, 5.5 melee weapons; ramp ≈ 147 M67. Risk of overflowing a dispenser/dropper
  (9 slots): ~1 in 1,200 in the police station hard barrel, 1 in 2,500 in the police station barrel, 1 in 8,800 in the
  building barrel.

## Police station with throwables x2 (16 Nov 2026)
- Request: "in the police station, double the chances of the throwables" (M67, RGN, C4;
  `GEAR_THEME_MULT = {"police_station": {"throwable": 2.0}}`) and "put melee items in the houses too".
  **Melee weapons already dropped in houses** (rule: every theme except the pharmacy, 2% each); nothing was changed
  for them, the user was told and received a table of multipliers.
- Validated (3,000 chests): police station M67 17.8%, RGN 8.9%, C4 6.1%, melee weapons 1.7–2.1%; house and building
  unchanged; 0 load errors. Whole police station (63 containers): ~46 M67, ~15.5 RGN, ~3.8 C4.
- Risk of overflowing a dispenser/dropper (9 slots) in the police station: ~1 in 1,200 (barrel) and 1 in 610 (hard
  barrel).

## Healing rarity doubled and the new Epic class (16 Nov 2026)
- Request: "double the rarity of the healing items, keep the pharmacy as it is" (interpreted: items 2x rarer = chances
  x0.5, LesRaisins and First Aid, pharmacy with the same numbers as before); CMS, AI-2 and Morphine -> Rare; SURV12 and
  Morphine Injector -> new **Epic** class. The Rare/Epic numbers were my choice. Milk, bread, equipment and ammo
  unchanged.
- Config: `HEAL_RARITY_SCALE = 0.5`, `HEAL_PHARMACY_FIXED` (the old `PHARMACY_MULT` was removed).
- Validated (building, 8,000 chests): plaster 7.8%, Common 4.2–5.3%, blood pack 2.2%, CAR 2.1%, AI-2 and CMS 0.9%,
  SURV12 0.6%, defibrillator 2.3%, morphine 1.1%, injector 0.5%; pharmacy (3,000) identical to before (CMS 6.8%,
  SURV12 4.0%, plaster 15.1%). 0 load errors.
- Expected result: green tower ~23 LesRaisins healing items and ~98 First Aid units (before 50 and 199); 100 chests
  ~133 healing items in total; chance of 1+ Epic item in 100 chests 39% each, Rare 63% each.

## Attachments by rarity class (16 Nov 2026)
- User's idea: "slightly rarer than guns", based on the gun type the attachment fits and its attributes. Proposal
  (table) approved and applied unchanged. Before: att = 4% (building chest, 1/3 of the gun) and 1.2% in barrels (3x the
  gun), type with a fixed weight and uniform within the type. Now: 9.6% and 0.3%.
- Facts: compatibility comes from `tacz_tags/attachments/allow_attachments/<gun>.json` (`#tacz:...` tags resolved
  recursively); attributes from `data/attachments/<id>_data.json` and zoom from
  `assets/tacz/display/attachments/<id>_display.json`. 67 of the 71 guns have a list (`m320`, `minigun`, `rpg7`,
  `taurus943` accept no attachment); `sight_infitac_fmp13` has no data file. The special ammo (fmj, he, hp, i, slug...)
  is of type `extended_mag` in TACZ. Epic: scope_mk5hd, scope_xl50, scope_mk4ert, scope_1873_6x, scope_1866_4x,
  muzzle_silencer_vulture, muzzle_brake_timeless50, laser_peq6, stock_heavy_spas_12, stock_tactical_spas_12. The
  attribute weights and the 40/30/20/10 cuts are my judgment (approved by the user).
- Validated on the server: building (8,000 chests) 9.6% with an attachment, classes 67.8/22.2/8.1/1.9% (expected
  65.6/24.2/8.2/2.0); per item 0.155/0.069/0.037/0.019%; police station (3,000) 19.9% (Epic came out below the
  expected, small sample). If the TACZ catalog changes, run `tools/att_rarity.py` (the generator fails if the classes
  are out of date). (This system was replaced on 17 Nov 2026 and `tools/att_rarity.py` was removed.)

## Guns spawn with 50% of the magazine (16 Nov 2026)
- Request: "all guns, except the minigun, now spawn with 50% of a full magazine". `GUN_SPAWN_AMMO_FRACTION = 0.5`,
  `GUN_SPAWN_AMMO_EXCLUDED = ("minigun",)`, `gun_spawn_ammo()`. Magazine = TACZ `ammo_amount`
  (`docs/tacz_catalog.json`); only the minigun has none. Rounding UP (my choice): 22 guns have an odd magazine; 4 have a
  magazine of 1 (lonetrail, m320, rpg7, springfield1873) and spawn loaded with 1. The round in the chamber
  (`HasBulletInBarrel`) stays false.
- Validated on the server: 1,280 sampled guns (all 70 appeared), all with the expected count; minigun 0; 0 load
  errors. **ERROR fixed in 1.0.1:** in 1.0.0 the magazine came out EMPTY in game (see the section "Empty magazine in
  1.0.0"); the earlier approval had not checked the magazine.
- This interacts with the ammo pool: the gun already carries rounds, but the reserve ammo is still drawn separately.

## Barrels with half the chance (16 Nov 2026)
- User's question: "is the rule of barrels giving 50% less loot still active?" **That rule did not exist in this mod**
  (it may have been from the old mod, deleted). There were: barrels with 3% to 25% of the chest's guns/ammo/attachments,
  and the AMC rule of removing 70% of the buildings' barrels (AMC commit of 2026-11-14 "Barrels of the buildings: 70%
  taken out, the others chests, copy by copy"; only for buildings). Request: "apply barrels with half the chance in
  those categories".
- Implemented in `item_chances`/`fa_chances` (parameter `tier`). For the half to be exact at low chances (SURV12 barrel
  0.25%) the per-item draws got a 10x finer resolution (`ITEM_RES = 10`: total weight 10,000; `item_prob()` does the
  real math). (Later `ITEM_RES = 100`.) The chance of drawing ANY item per container did not change in chests.
- Validated on the server: building barrel (6,000) M67 4.6%, milk 4.1%, plaster 4.2%, SURV12 0.3%; house barrel bread
  9.3%; pharmacy barrel vaseline 4.4%, SURV12 1.9%; building chest unchanged (M67 9.6%).
- Effect per structure (before -> after, LR healing / First Aid / grenades+melee): average workshop 15.7->8.0 / 67->34 /
  36->18; large pharmacy 16.9->9.9 / 53->31; house 14.4->8.6 / 62->37; ramp 100.9->70.3 / 431->300; green tower (no
  barrels) unchanged. The risk of overflowing a dispenser/dropper goes down (fewer items per barrel).

## Empty magazine in 1.0.0 — fixed in 1.0.1 (16 Nov 2026)
- Symptom reported by the user: loot guns with an empty magazine (HUD `000`), although `/data get entity @s
  SelectedItem` showed `GunCurrentAmmoCount: 5b`.
- **Cause (confirmed in the bytecode):** TACZ only reads the magazine if the tag is an **integer**
  (`GunItemDataAccessor.getCurrentAmmoCount`: `contains("GunCurrentAmmoCount", 3)`, 3 = TAG_INT). A small number written
  as a JSON object in `minecraft:custom_data` becomes a **byte** (`5b`), so TACZ saw 0.
- **Fix:** `e_gun` writes the gun's `custom_data` as **SNBT text**
  (`{GunId:"tacz:x",GunFireMode:"SEMI",GunCurrentAmmoCount:15,HasBulletInBarrel:0b}`), where `15` is an integer.
- **My test mistake:** the validations read the value with the regex `(\d+)` and ignored the type suffix (`b`, `s`,
  `L`). Now: also check the **type** of every numeric tag another mod reads. Validated (real chest, 1,200 chests): 405
  guns, 66 models, all with an integer magazine and the right amount.
- General rule: for any number inside `custom_data` that another mod reads, use SNBT (or check in the bytecode the type
  it expects).

## AMC: chests drawn per copy (check of 16 Nov 2026)
- AMC commits of 2026-11-15 "Chests saved in the buildings' templates taken out (procedural chests, stage 1)" through
  2026-11-16 "Barrels that hold something stay barrels (too many chests on the tower's ground...)": chests saved in the
  templates of the 10 buildings removed and drawn per copy (`core/ChestDraw`, ranges by height class), "hard" for those
  drawn underground or on the terrace, barrels that hold something stay barrels; spawn categories by height.
  `Palette.lootTable` still `chests/<theme>/<tier>[_hard]` and `LOOT_THEMES` the same: **no change needed in the
  mod**. The AMC jar used in the measurement was identical (cmp) to the one in the user's instance.
- Mean count (no pots), old -> new: apartments 10->23, skeleton 17->22, small 24->26, bluish 16->61, apocalyptic
  49->66, tower 71->102, green tower 91->80, crash 94->94, wide 161->93, brutalist 229->133; ramp 399 and police station
  63 the same. Since the chances are per chest, the feeling per chest does not change; the total per building does
  (e.g. guns in the brutalist 27.5->16.0; in the bluish 2.0->7.3).

## Healing out of workshop/gas station/police station and milk 1–3 (16 Nov 2026)
- Validated on the server (1,500 containers each): police station chest, workshop barrel and gas station barrel
  without any LesRaisins or First Aid healing; milk present with 1–3; building chest with the normal healing. 41 tables
  and 36 loot modifiers (without the 12 `_firstaid` tables of those 3 themes). 0 load errors.
- Milk only in buildings and houses (16 Nov): validated (1,200 containers each): pharmacy, police station, workshop and
  gas station without milk; building 7.5% and house 8.1%, with 1–3.

## Vanilla tools in the workshop (16 Nov 2026)
- Request: Rare iron pickaxe and flint and steel (40–65% durability), Legendary netherite pickaxe (100%); proposal with
  option A (barrels with half, like the barrel rule) approved. `set_damage` uses the fraction of durability LEFT (1.0 =
  undamaged).
- Validated (3,000 workshop chests and 3,000 barrels): iron 1.07% / 0.43%, flint and steel 0.93% / 0.60%, observed
  durability 41–66% (flint and steel has 64 uses: rounding reaches 65.6%). Netherite did not drop in 6,000 samples
  (expected ~2.25; chance of zero ~10%): checked only by the table weights (0.050% / 0.025%). Per workshop: iron and
  flint and steel 27% (average) / 19% (small); netherite ~1 in 64 average workshops.

## Milk 4% and bread 16% with 1–5 (17 Nov 2026)
- User's request (their numbers): condensed milk 8% -> 4% and bread 20% -> 16%, bread amount 4–12 -> 1–5; barrels
  proportional (half: milk 2%, bread 8%). Only `FOOD` in `tools/gen_loot.py`; 8 tables changed (`building` and
  `house`, `chest`/`chest_hard`/`barrel`/`barrel_hard` `_core`).
- Validated on the server (3,000 containers each, Luck 0): building chest milk 3.6%; house chest milk 3.7% and bread
  16.0% (1–5, mean 3.0); building barrel milk 1.9%; house barrel milk 1.6% and bread 7.8%. No load errors.

## Gun rarity rework: categories + 5 levels (17 Nov 2026, v1.0.1)
- User's request (file on the desktop + "Categorize those dmr as rifle" + "Option A, keep 16.8%, you can apply"): DMR
  becomes rifle; 5 levels per category; total chance per category in the building = their "1 in N".
- Weight per gun = category share x LEVEL_W[level] / sum of the category's weights (total sum 100,000). Level per gun in
  `GUN_LEVELS` (all 70 guns; golden deagle Epic and springfield1873 Uncommon were my choice).
- Side effects (communicated): (1) total building guns 12% -> 16.8%; (2) building attachments frozen (do not go up);
  (3) ammo follows the gun popularity (`ammo_weights` uses `gun_weights`): caliber shares changed (building: 12g
  11.9->9.2%, .45 ACP 9.3->6.6%, .50 AE 4.3->2.6%, 40mm and rocket 2.4->4.3%, 4.6x30 3.8->6.1%); the total ammo chance
  per container did NOT change; (4) `docs/attachments_rarity.json` (which used the old gun weights as "popularity") was
  NOT regenerated.
- Resulting chances (building, chest): Common 5.68%, Uncommon 5.21%, Rare 2.83%, Epic 2.77%, Legendary 0.31% (1 in
  319); 100 chests: 27% of having >= 1 Legendary. Per gun (Option A): Common rifle 0.30% (1/333) ... Legendary rifle
  0.019% (1/5,334); explosives (Epic only) 0.714% each (1/140).
- Validated on the server (Luck 0, 0 load errors): 40,000 building chests -> 6,716 guns (expected 6,736), levels
  5.70/5.27/2.62/2.89/0.31%; 80,000 chests -> per category within 2 deviations; police station 20,000 chests -> 5,035
  guns (expected 5,000), levels Common 10.0 / Uncommon 7.7 / Rare 5.0 / Epic 2.1 / Legendary 0.34%. A −2.5 deviation in
  rifles in the 1st sample disappeared in the 2nd (noise).

## Police station: guns 2x the building (17 Nov 2026, v1.0.1)
- User's request: "in the police station, the chances of all guns, regardless of category and rarity level, will be
  multiplied by 2". The police station uses the same profile as the building: chest 336‰, hard 562‰, barrel 12‰, hard
  barrel 20‰ (`RATES["police_station"]`).
- **Police station attachments: stay as they were** (200/266/24/48‰ explicit in `att`; "will stay 2x", but they are
  actually 2.08x / 1.66x / 8x / 8x the building's) and **so does the ammo chance per container** (80 / 100 / 20 / 36%).
  The police station caliber mix is now the SAME as the building (`pick/ammo_default`; `ammo_police` and `gun_police`
  no longer exist). User: "ammo and attachments, we will look at more calmly later".
- Validated on the server (Luck 0, 0 load errors): chest 40,000 -> 33.38% guns (expected 33.6%); hard chest 20,000 ->
  55.98% (56.2%); barrel 60,000 -> 1.21% (1.2%); hard barrel 40,000 -> 1.93% (2.0%).
  Attachments measured 20.1 / 26.3 / 2.4 / 5.0%. Levels in chests: Common 11.5%, Uncommon 10.3%, Rare 5.5%, Epic 5.5%,
  Legendary 0.57% (expected 0.62%, 1 in 160 chests).

## Attachments redefined from the user's structures (17 Nov 2026, v1.0.1)
- File `Desktop/TACZ_attachments.txt` + 7 `.nbt` files (in the `generated/minecraft/structures/` folder of the user's
  test instance: base = color legend; tacz_scopes, tacz_extended_mag with level; grip, laser, muzzle, stock without).
  User's choices: unrated = the Uncommon weight (option B), levels 16/8/4/2/1 (Mythic 0.5 was my proposal, accepted),
  include the 9 non-craftable items, leave out the 4 craftable items not listed. `stock_m4ss` was duplicated (counts
  once).
- Removed `tools/att_rarity.py` and `docs/attachments_proposta.csv` (old 2-factor classification, replaced). The old
  "0.8 x gun" rule and the freezing of the building attachments ended.
- Validated on the server (Luck 0, 0 load errors): building chest 80,000 -> attachments 20.25% (expected 20.2%), guns
  16.83%; hard 30,000 -> 33.78% / 28.40%; barrel 60,000 -> 0.69% / 0.61%; police station chest 40,000 -> 40.33% /
  33.45%, hard 30,000 -> 66.85% / 56.07%, barrel 60,000 -> 1.44% / 1.15%. Levels (building chest, measured/expected):
  Common 8.01/8.10, unrated 9.63/9.58, Rare 1.30/1.29, Epic 0.55/0.55, Legendary 0.131/0.115, Mythic 0.018/0.012 (14
  `ammo_mod_he` in 80,000 chests).

## Ammo by level + police station with the building's ammo chance (17 Nov 2026, v1.0.1)
- User's request: they classified the 23 calibers by concrete color in `tacz_ammo.nbt` (same rule as the
  attachments), "weights 16/8/4/2/1" and "you can apply the police station together" (police ammo = the building's
  chances). The amounts inside their chests are just the full stack size (7.92x57 was 34 instead of 36: a typo,
  ignored). Calibers 7.62x25 and 6.8x51 Fury (no gun in the loot) stay out. The old mix (50% equal + 50% gun popularity)
  and `AMMO_MIX_UNIFORM` were removed; `ammo_police` no longer exists.
- Validated on the server (Luck 0, 0 load errors): building chest 60,000 -> 51.87% with ammo (expected 52%), 34.06
  rounds/container (34.1); police station chest 60,000 -> 52.06% / 34.03; hard 30,000 -> 86.3% (86.6%) in building and
  police station; police station barrel 60,000 -> 6.16% (6.2%), hard barrel 40,000 -> 11.26% (11.4%). Per caliber
  (building chest, measured/expected): 9mm 11.2/11.1, 12g 5.71/5.76, .308 1.47/1.48, 40mm 1.39/1.48, rocket 1.52/1.48,
  .50 BMG 442 times in 60,000 (447 expected).
- Consequence (communicated): police station barrels lose ammo (barrel 11.8 -> 4.1 rounds, hard 21.2 -> 7.5); chest
  47.1 -> 34.1. The building goes up ~11% in rounds per container (large-stack calibers became more common).
- Adjustment the same day (user: ".50 BMG 21-30; lower the Legendary rarity a bit: 1/100 instead of 1/134"):
  `AMMO_LEVEL_W["Lendário"]` 1 -> 1.35 (the only Legendary is the .50 BMG; the other 22 calibers lose ~0.2% share) and
  `AMMO_RANGE_OVERRIDE = {"50bmg": (21, 30)}` (before 12-25; max stack 30). Validated (80,000 chests each, Luck 0):
  building 1.03% (824 chests, stacks 21-30, mean 25.5), police station 1.00% (803; expected 1.00%). A stack of 16
  appeared in the police station: two draws of the same caliber in the same chest add up in `/loot insert` (limit 30),
  an artifact of the test, not of the table.

## Backpacks (Sophisticated Backpacks) and flashlights (TCT Flashlight) in houses — version 1.1.0 (17 Nov 2026)
- User's request: two OPTIONAL dependencies; levels in `backpacks.nbt` and `flashlight.nbt` (same `structures` folder
  as the others); "items exclusive to houses"; "1 in N" is the chance, per chest, of **EACH ITEM** of that level (the
  1st version, which read the number as the chance of the whole level split among its items, was CORRECTED by the user
  the same day).
  Backpacks (**FINAL VALUES, 17 Nov 2026, per item**): Common 1/9, Uncommon 1/14, Rare 1/20, Epic 1/30, Legendary 1/54.
  Flashlights: Uncommon 1/10, Rare 1/16. (Before: 15/30/45/75/120 and 30/45.) Config: `LEVEL_FAMILIES` and
  `BACKPACK_COMPONENTS` in `tools/gen_loot.py`.
- Items per level: Common `copper_backpack`; Uncommon `iron_backpack`, `stack_upgrade_tier_1`; Rare `gold_backpack`,
  `advanced_pickup_upgrade`, `stack_upgrade_tier_2`; Epic `diamond_backpack`, `stack_upgrade_tier_3`; Legendary
  `netherite_backpack`, `inception_upgrade`, `stack_upgrade_tier_4`. Flashlights: Uncommon `flashlight_off`; Rare
  `headlamp_helmet`, `night_vision_goggles_helmet`. Backpacks come with the components of the user's chests
  (`sophisticatedcore:number_of_upgrade_slots` / `number_of_inventory_slots`: 1/45, 2/54, 3/81, 5/108, 7/120).
- My choices (not answered by the user): SEPARATE items (no backpack comes with an upgrade inside); unclassified items
  stay out (basic `backpack`, the other upgrades, `battery`, `lantern`, the lit `flashlight`); hard chest = chest;
  barrels with half (BARREL_ITEM_MULT).
- Tables `house/<tier>_backpacks` and `house/<tier>_flashlight` (one independent pool per ITEM) + 8 loot modifiers in
  total (4 per family), with `neoforge:conditions` `mod_loaded` (`sophisticatedbackpacks` / `flashlight`); the mod
  gained 2 optional dependencies in `neoforge.mods.toml`; version 1.0.1 -> 1.1.0.
  The generator's `check()` requires the `mod_loaded` condition in any table with an item from these mods. Total now 47
  tables and 44 loot modifiers.
- Test: the dev server (NeoForge 21.1.219) does NOT load Sophisticated Backpacks (it needs >= 21.1.229): to test with
  the mods run `./gradlew runServer -Pneo_version=21.1.264` (the version of the user's instance; only for the test,
  `gradle.properties` did not change) and copy into `run/mods/` `sophisticatedbackpacks` and `sophisticatedcore` (AMC
  libs) and `flashlight-5.0` and `tctcore-2.3` (from the user's test instance). Known warning unrelated to the mod:
  `Couldn't load tag minecraft:placeable ... tacz:blood_strike_1`.
- Validated on the server (Luck 0), final version (chance per ITEM): WITHOUT the optional mods: 0 load errors and none
  of their items. WITH the mods: 0 errors; house chest 60,000 -> measured/expected: copper 6.64/6.67%, iron 3.20/3.33,
  stack1 3.33/3.33, gold 2.20/2.22, diamond 1.31/1.33, netherite 0.88/0.83, inception 0.83/0.83, Flashlight 3.24/3.33,
  Headlamp 2.23/2.22, NVG 2.19/2.22; hard chest 30,000 and barrel 60,000 (half) match; building, police station,
  workshop, gas station and pharmacy: none of these items; the 5 backpack types come with the right components. Any
  backpack item per house chest 22.6%; any flashlight 7.6%. Risk of overflowing a 9-slot barrel in the house: 1 in 38
  million -> 1 in 5.4 million (exact enumeration; a different method from the old one).
- Flashlight battery: `flashlight:battery` is craftable (5 from 1 redstone block + iron) and is an ingredient of the
  Flashlight, Headlamp and NVG; the code stores `BatteryFlashlight`, but whether/how it uses charge was NOT verified:
  test in game.
- **Final values (17 Nov 2026, "I want to change all the rarities")**: validated (60,000 house chests,
  measured/expected): copper 11.07/11.11%, iron 7.16/7.14, gold 4.96/5.00, diamond 3.35/3.33, netherite 1.86/1.85,
  Flashlight 10.09/10.00, Headlamp 6.16/6.25; hard chest 30,000 and barrel 60,000 (half) match; 0 load errors. Any
  backpack item per house chest 41.9%; any flashlight 20.9%. Risk of overflowing a 9-slot barrel in the house: 1 in ~1
  million (exact enumeration).
- **17 Nov 2026: the backpacks and flashlights stage (v1.1.0) was tested and approved by the user** ("Tested and
  approved, you can close this stage"). Not pushed yet then (commits of 17 Nov 2026 "CLAUDE.md: etapa de
  armas/anexos/municao por nivel fechada e aprovada", "Mochilas (Sophisticated Backpacks) e lanternas (TCT Flashlight)
  opcionais nas casas", "Mochilas e lanternas: chance por ITEM (correcao do usuario), nao por nivel", "Mochilas
  1/9,14,20,30,54 e lanternas 1/10,16 (por item)") and no GitHub release.

## TACZ ammo boxes: iron, gold, diamond (17 Nov 2026, v1.1.0)
- User's request: iron ammo box (Uncommon), gold (Rare), diamond (Epic); "Option B, only buildings and police
  station, police station with the same chances". Empty `tacz:ammo_box` item with `custom_data` `{Level:0|1|2}` in SNBT
  (integer Level; the same form as the TACZ recipes). Config `AMMO_BOX` in `tools/gen_loot.py`.
- Chance of EACH box per chest (hard chest = chest; barrels half): iron 1/14 (7.14%), gold 1/20 (5%), diamond 1/30
  (3.33%) = the same numbers as the backpacks; any box 14.7% per chest. Only `building` and `police_station`, no mod
  condition (TACZ required). Not included: house, workshop, gas station, pharmacy.
- Validated on the server (Luck 0, 0 load errors): building chest 60,000 -> iron 7.10 / gold 5.07 / diamond 3.33%; hard
  chest 30,000 -> 7.11 / 4.98 / 3.29; barrel 60,000 -> 3.62 / 2.64 / 1.70 (expected 3.57 / 2.5 / 1.67); police station
  chest 60,000 -> 7.09 / 4.98 / 3.34 and barrel 3.57 / 2.65 / 1.62; house and workshop: none. `Level` comes out as an
  integer (`{Level: 1}`, no byte suffix). Box capacity NOT verified (TACZ config). Risk of overflowing a 9-slot barrel
  (exact enumeration, without and with the boxes): building hard barrel 1 in 534 thousand -> 1 in 302 thousand; police
  station hard barrel 1 in 1.6 million -> 1 in 724 thousand.
- **17 Nov 2026: the ammo boxes stage (v1.1.0) was tested and approved by the user** ("Tested and approved, you can
  close this stage"). State: v1.1.0 complete and approved; not pushed yet then (commits of 17 Nov 2026 from "CLAUDE.md:
  etapa de armas/anexos/municao por nivel fechada e aprovada" to "Caixas de municao do TACZ (ferro/ouro/diamante) em
  predios e delegacia") and no GitHub release.

## Baseball bat slightly rarer than the dagger (18 Nov 2026)
- User's request ("slightly rarer than the dagger") and choice "Option B": baseball bat 2.0% -> **1.5%** per chest (1
  in 67; barrel 1.0% -> 0.75%, 1 in 133); dagger and karambit stay at 2.0% / 1.0%. `GEAR["baseball_bat"]["p"]` 20 -> 15;
  applies in every theme with melee weapons (all except the pharmacy); hard chest = chest.
- Validated on the server (Luck 0, 0 load errors): building chest 60,000 -> bat 1.55%, dagger 1.9%, karambit 2.0%; house
  barrel 60,000 -> 0.76% / 1.0% / 0.9%; police station hard chest 30,000 -> 1.55% / 2.1% / 2.0%.
- The rebuilt `amctaczloot-1.1.0.jar` differs from the one attached to the v1.1.0 release (which still has the bat at
  2.0%): the release was NOT updated.
- **Version 1.1.1 (18 Nov 2026):** `mod_version` 1.1.0 -> 1.1.1 only to publish the bat at 1.5% (the jar attached to
  the v1.1.0 release still had 2.0%); jar `amctaczloot-1.1.1.jar` (loads without errors; backpacks still drop). Push and
  release v1.1.1 done at the user's request.

## Throwables only in the building and the police station (18 Nov 2026)
- User's request: "keep the throwables only in the building and the police station".
  `THROWABLE_THEMES = ("building", "police_station")` in `tools/gen_loot.py`: M67 (3-5), RGN (2-4) and C4 drop ONLY in
  those two themes, with the same chances as before (building chest 9.2 / 4.1 / 3.0%, barrel half; police station
  double); house, workshop, gas station and pharmacy have no throwables. Melee weapons (dagger, karambit, bat) stay in
  every theme except the pharmacy. 12 tables changed (house, workshop and gas station).
- Validated on the server (Luck 0, 0 load errors, 20,000 chests each): building M67 8.8% / RGN 4.1% / C4 3.1%; police
  station 18.6% / 8.2% / 5.8%; house, workshop (barrel) and gas station: no throwables, melee weapons present (dagger
  ~2%, bat ~1.5%); pharmacy (5,000): nothing.
- The rebuilt `amctaczloot-1.1.1.jar` differs from the one attached to the v1.1.1 release (which still has throwables
  in the other themes); release NOT updated.

## Backpacks: rarity PER ITEM and no Inception (18 Nov 2026)
- User's request ("New update of the backpack and upgrade rarities"): "1 in N" of EACH item, per house chest (hard
  chest = chest; barrel half): Copper Backpack 13, Iron 20, Gold 32, Diamond 45, Netherite 57; Stack Upgrade tier 1 26,
  tier 2 52, tier 3 63, tier 4 79; Advanced Pickup 29.
  **Inception Upgrade removed** (was Legendary 1/54). The Common to Legendary levels no longer set the chance (each item
  has its own). `LEVEL_FAMILIES` in `tools/gen_loot.py` became `item -> (level, N)`; flashlights unchanged (Flashlight
  10, Headlamp 16, NVG 16).
- Validated on the server (Luck 0, 0 load errors, house chest 60,000, measured/expected): copper 7.58/7.69%, iron
  4.97/5.00, gold 2.98/3.12, diamond 2.27/2.22, netherite 1.77/1.75, stack1 3.77/3.85, stack2 1.94/1.92, stack3
  1.57/1.59, stack4 1.25/1.27, pickup 3.43/3.45; hard chest 30,000 and barrel 60,000 match; Inception 0.
- The rebuilt `amctaczloot-1.1.1.jar` differs from the one attached to the v1.1.1 release; release NOT updated.
- **Backpack barrels (18 Nov 2026):** user's request "the backpack rarity stays the same as the chests in barrels"
  and then "and the upgrades too": the `backpacks` family (5 backpacks + 4 upgrades) has the SAME chance in barrels as
  in chests (`barrel_mult=1.0` in `LEVEL_FAMILIES`). Flashlights keep half in barrels.
  Validated (house barrel 60,000 / hard barrel 30,000, Luck 0): copper 7.89 / 7.71%, iron 5.07 / 4.79, gold 3.01 / 3.19,
  diamond 2.21 / 2.19, netherite 1.76 / 1.82, stack1 3.86 / 3.79, stack2 1.97 / 1.99, stack3 1.60 / 1.67, stack4 1.17 /
  1.30, pickup 3.48 / 3.27 (expected equal to the chest); Flashlight in the barrel 4.89 / 4.80% (half of 10%). Risk of
  overflowing a 9-slot barrel in the house: 1 in 8.8 million (exact enumeration), mean 1.26 stacks.

## Version 1.1.2 (18 Nov 2026)
- `mod_version` 1.1.1 -> 1.1.2 to publish: throwables only in building and police station, backpacks and upgrades with
  per-item rarity and no Inception, backpacks/upgrades with the chest chance in barrels. Jar `amctaczloot-1.1.2.jar`
  (loads without errors; Inception absent; backpacks and melee weapons drop; no throwables in houses).
  Push and release v1.1.2 done at the user's request; the v1.1.1 (and v1.1.0) releases stay published with the old
  content.
- **18 Nov 2026: the stage of backpacks, throwables and v1.1.2 was tested and approved by the user** ("Tested and
  approved, you can close this stage"). Next stage (pre-release): code review, security, optimization, bugs and
  translation of the documents into English.
- The pre-release review was done on 18 Nov 2026 in the `revisao-pre-lancamento` branch (see `CLAUDE.md`).
