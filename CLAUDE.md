# AMC TACZ Loot — working rules and current state

## Working rules (mandatory; chosen by the user on 13 Nov 2026, same as the Abandoned Modern City project)
1. **Ask along the way**: design decisions, numbers and style belong to the user; when there is more than one solution,
   present options.
2. **Build the `.jar` after every small/medium change** (`./gradlew build` → `build/libs/`) and say what changed in it.
3. **GitHub** (`gh`): frequent, clear commits; update the repository with every testable jar (push only when the user
   asks).
4. **Iterative**: small, testable steps; at the end of each one, a summary + the recommended next step.
5. **Do not move to the next step before the user tests and approves the current one.**
6. **Documentation always up to date** (this file, `README.md`) in the same commit as the change.
The user is not a programmer: explain in plain language. The user's own global rules (`~/.claude/CLAUDE.md`) also apply.

## What it is
A **data-only** mod (NeoForge 1.21.1, `modLoader="lowcodefml"`, no Java), mod id `amctaczloot`, that adds loot to the
Abandoned Modern City (AMC) container tables (`abandonedmoderncity:chests/<theme>/<chest|barrel|pot>[_hard]`): TACZ
guns, ammo, attachments and ammo boxes; LesRaisins healing, grenades, C4 and melee weapons; optional items from First
Aid, Sophisticated Backpacks and TCT Flashlight. It also **overrides the 36 AMC tables with junk only**, so no useful
vanilla item is left. Themes: building, police_station, pharmacy, house, workshop, gas_station. Decorated pots get
nothing from the mod. The history of every decision (13 to 18 Nov 2026) is in `docs/HISTORY.md`.

## Current state (version 1.0.0, the first public release; 18 Nov 2026)
- Versions 1.0.0 to 1.1.2 mentioned in `docs/HISTORY.md` were **internal test versions** (private releases, never downloaded by
  anyone else); their releases and tags are to be deleted before the public 1.0.0 is published (user's decision, 18 Nov 2026).
- Mod icon: `src/main/resources/icon.png` (512x512, transparent), referenced by `logoFile` in `neoforge.mods.toml`.
- **Requires** AMC 1.0.0+ (`[1.0.0,)`; the game refuses to load the mod with AMC 0.1.0, tested), TACZ 1.2.0+,
  LesRaisins 0.4.3+. **Optional**: First Aid 1.3.5+, Sophisticated Backpacks 3.26.21+ (needs NeoForge 21.1.229+), TCT
  Flashlight 5.0+. Author `RakkuLyc`, license MIT (`LICENSE`).
- **All numbers live in the top block of `tools/gen_loot.py`**; the loot values per item are summarized in `README.md`.
  Main values (per container, Luck 0, chest / hard chest): guns building 16.8% / 28.1%, police station 33.6% / 56.2%;
  attachments = 1.2x guns; ammo 52% / 86.6% in building and police station (1 to 3 stacks), workshop 4% / 7%; ammo boxes
  1 in 14 / 20 / 30 (building, police station); LesRaisins healing 0.5-4.6% per item (pharmacy 4.0-9.2%), none in
  workshop, gas station, police station; First Aid 0.5-7.5% (pharmacy 4.0-15%); M67/RGN/C4 9.2/4.1/3.0% in buildings,
  2x in the police station; melee 2.0/2.0/1.5% everywhere except the pharmacy; milk 4% (building, house), bread 16%
  (house); workshop tools 1.0/1.0/0.05%; backpacks 1 in 13 to 1 in 79 and flashlights 1 in 10/16/16 (houses). Barrels:
  per-item chances halved, except backpacks (same as chests); guns/ammo/attachments much rarer (RATES).
- Gun rarity: 7 categories (`GUN_CAT_ONE_IN`) x 5 levels (`GUN_LEVELS`, `LEVEL_W` 16/8/4/2/1). Calibers by level
  (`docs/ammo_rarity.json`, `AMMO_LEVEL_W`, .50 BMG 1.35 and 21-30 rounds); attachments by level (109 items,
  `docs/attachments_rarity.json`, `ATT_LEVEL_W`). Guns spawn with half a magazine (minigun 0).
- The level names in the data stay in Portuguese (Comum, Incomum, Raro, Épico, Lendário, Mítico, Sem raridade =
  Common, Uncommon, Rare, Epic, Legendary, Mythic, unrated): the generator reads them from `docs/*.json`.
- The user's source `.nbt` structures (for `tools/att_from_nbt.py`) no longer exist anywhere (searched the whole disk and both
  trash bins on 19 Nov 2026; the user has no backup). `docs/ammo_rarity.json` and `docs/attachments_rarity.json` are the only
  copies (safe in git): to change a level, edit the JSON directly. The normal path of `att_from_nbt.py` was never re-tested.
- **Pre-release review (18 Nov 2026)**, branch `revisao-pre-lancamento`, not merged or pushed: bugs fixed (RCON reading
  of long replies, sampler with exact counts, tools writing `docs/` from any folder), automated tests, Gradle
  distribution checksum, dead code removed, `gen_loot.py` reorganized and translated, containers re-measured with AMC
  1.0.0, English documentation. The loot did not change (the 128 generated files are identical; only `mods.toml` changed:
  author, AMC range, version). Pending for the user: merge, push, deleting the old internal releases/tags, release 1.0.0, repository visibility, and the final
  rewrite of the commit email (needs a force push and moving the release tags).

## Verified facts (checked in the jars, the Minecraft source or in game; details in `docs/HISTORY.md`)
- Injection: `neoforge:add_table` global loot modifiers filtered by `neoforge:loot_table_id`, listed in
  `data/neoforge/loot_modifiers/global_loot_modifiers.json` (`replace:false`). The AMC tables are overridden by path;
  `mods.toml` declares `ordering="AFTER"` for the AMC.
- TACZ items are generic (`tacz:modern_kinetic_gun`, `tacz:ammo`, `tacz:attachment`, `tacz:ammo_box`) with the id in
  `minecraft:custom_data` (`GunId`, `AmmoId`, `AttachmentId`, `Level`). **Numbers another mod reads must be written as
  SNBT text**: a small JSON number becomes a byte (`5b`) and TACZ only reads `GunCurrentAmmoCount` as an integer (the
  empty-magazine bug of 1.0.0).
- LesRaisins: `lrtactical:consumable` (`ConsumableId`), `lrtactical:throwable` (`ThrowableId`), `lrtactical:melee`
  (`MeleeWeaponId`). Grenade max stack 3, C4 1. First Aid items are plain `firstaid:<id>` (max stack 16).
- Optional mods: the table AND the loot modifier need `neoforge:conditions` `mod_loaded`; without the mod the server
  starts normally and nothing from it appears (tested).
- Luck: effective weight = `floor(weight + quality*Luck)`, rolls = `rolls + floor(bonus_rolls*Luck)`; `quality` is 25%
  of the weight per level. `random_chance` ignores Luck. The console `/loot` and RCON tests are always Luck 0.
- A container with more stacks than slots keeps the first ones and loses the excess, picked at random
  (`LootTable.fill`). Dispensers and droppers (9 slots) get the AMC `barrel` table: worst case about 1 in 300,000;
  chests and barrels (27 slots) not affected in practice. Pots: `unpackLootTable(null)` (no Luck, 1 slot): left out.
- RCON (`RconClient`): the server reads one packet per network read and splits replies longer than 4096 bytes;
  `tools/rconlib.py` handles both.
- In a real chest Minecraft splits stacks into pieces over random slots (`shuffleAndSplitItems`); `/loot insert` does
  not, and it merges equal stacks.

## How to test
- **Automated tests (no server):** `python3 -m unittest -v` (`tests/test_loot.py`: files = generator, determinism,
  table structure, optional-mod conditions, loot modifiers, the 36 AMC tables, IDs in the catalogs, chance of each item
  = configuration, 9-slot overflow below 1 in 100,000).
- **Generator:** `python3 -I tools/gen_loot.py` (preview), `--write` (rewrites the data and runs `check()`).
- **Build:** `JAVA_HOME=/usr/lib/jvm/java-21-openjdk ./gradlew build -Dorg.gradle.java.installations.paths=$JAVA_HOME`
  (the system's default Java is 27, too new for Gradle). Never ship a jar built right after a `-Pneo_version` run
  without checking `META-INF/neoforge.mods.toml` (`versionRange="[21.1.219,)"`).
- **Test server:** `run/mods/` holds the AMC 1.0.0 jar (`../AbandonedModernCity/build/libs/`), TACZ, LesRaisins, First
  Aid, Sophisticated Backpacks + Core and TCT Flashlight + Core (`run/` is not versioned). With the optional mods start
  it with `./gradlew runServer -Pneo_version=21.1.264` (same Java options); RCON on 127.0.0.1:25575, password `teste`
  (or the `AMC_RCON_PASSWORD` environment variable). Commands: `python3 -I tools/rcon.py "<command>" ...`.
  **Always stop it with `python3 -I tools/rcon.py stop`** and check that port 25575 is free (`ss -ltn`).
  **Never kill the user's Minecraft (the Prism launcher shows up as `bootstraplauncher`).**
- **Chance per item:** `python3 -I tools/sample_items.py <theme/tier> [N] [filter] [--json out.json]` (exact counts; ammo
  boxes per level `#L0/#L1/#L2`; raw `GunCurrentAmmoCount` text). Luck 0 only.
- **Real Luck** only in game: `/amcs spawn police_station abandoned_police_station` twice, far apart, and open one with
  `/effect give @s minecraft:luck infinite 2`.
- Chunks generated before an AMC change keep the old table ids; opened containers have no table: test in a new world
  or with `/amcs spawn`.
- Known unrelated warning: `Couldn't load tag minecraft:placeable ... tacz:blood_strike_1`.

## Generator (`tools/gen_loot.py`) and data
- Writes `data/amctaczloot/loot_table/<theme>/<tier>_core.json` (gun, attachment and ammo pools + one pool per item),
  `<tier>_firstaid.json`, `house/<tier>_backpacks.json`, `house/<tier>_flashlight.json`, the pick tables in `pick/`,
  one loot modifier per table, and the 36 junk tables in `data/abandonedmoderncity/loot_table/chests/`. Tiers chest,
  chest_hard, barrel, barrel_hard (no pot). 47 tables, 44 loot modifiers.
- Inputs in `docs/`: `tacz_catalog.json` (`tools/tacz_catalog.py <tacz.jar>`), `ammo_rarity.json` and
  `attachments_rarity.json` (`tools/att_from_nbt.py <structures folder>`), `containers.json` (preview only;
  `tools/measure_containers.py <AMC index.txt> run/world [names [offset]]`; for structures with drawn chests the file
  holds the mean of several copies: measured with AMC 1.0.0 on 18 Nov 2026), `lr_catalog.json` (reference only).
