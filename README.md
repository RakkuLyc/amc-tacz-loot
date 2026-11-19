# AMC TACZ Loot

A data-only mod for **NeoForge 1.21.1** that fills the containers of
Abandoned Modern City (AMC) with loot from **TACZ** (guns, ammo, attachments, ammo
boxes) and **LesRaisins Tactical Equipments** (healing, grenades, C4, melee weapons), plus optional items from
**First Aid**, **Sophisticated Backpacks** and **TCT Flashlight**.

**Version 1.0.0**, the first public release (requires AMC 1.0.0). License: MIT (see `LICENSE`).

## Requirements

| Mod | Version | |
|---|---|---|
| NeoForge (Minecraft 1.21.1) | 21.1.219+ | required |
| Abandoned Modern City | 1.0.0+ | required |
| TACZ (Timeless and Classics Zero) | 1.2.0+ | required |
| LesRaisins Tactical Equipments | 0.4.3+ | required |
| First Aid | 1.3.5+ | optional |
| Sophisticated Backpacks (with Sophisticated Core) | 3.26.21+ | optional (needs NeoForge 21.1.229+) |
| TCT Flashlight (with TCT Core) | 5.0+ | optional |

Only the TACZ default gun pack is used (70 guns). The game refuses to load this mod with an AMC older than 1.0.0.

## Installation

1. Install the required mods above, then put `amctaczloot-1.0.0.jar` in the `mods` folder (client and server).
2. Optional mods can be added or removed at any time: their loot is behind a `neoforge:mod_loaded` condition, so
   without them nothing from them appears and nothing breaks.
3. Use a **new world**, or newly generated areas. Containers keep the loot table id they got when they were placed,
   and a container that was already opened has no loot table anymore.

## What it does

The mod adds loot to the AMC container tables (`abandonedmoderncity:chests/<theme>/<chest|barrel>[_hard]`) with
NeoForge global loot modifiers, and **overrides the AMC tables with junk only** (sticks, seeds, rotten flesh, bones,
paper, bowls, glass bottles, spider eyes), so no useful vanilla item is left: the value comes from the mods.
Decorated pots get nothing from this mod.

Chances below are **per container, at Luck 0**. "Hard" containers are the AMC containers that are hard to reach
(underground, terraces, attics). Every item is an independent draw unless noted.

| Loot | Where | Chest / hard chest |
|---|---|---|
| Guns (TACZ) | building | 16.8% / 28.1% (1 in 5.95 / 1 in 3.6) |
| | police station | 33.6% / 56.2% (2x the building) |
| Attachments (TACZ) | building / police station | 1.2x the gun chance: 20.2% / 33.7%; police station 40.3% / 67.4% |
| Ammo (TACZ), 1 to 3 stacks | building, police station | 52% / 86.6% |
| | workshop | 4% / 7% |
| Ammo boxes (TACZ, empty): iron, gold, diamond | building, police station | 1 in 14, 1 in 20, 1 in 30 each |
| LesRaisins healing (9 items) | building, house | 0.5% to 4.6% per item |
| | pharmacy | 4.0% to 9.2% per item |
| First Aid healing (7 items, optional) | building, house | 0.5% to 7.5% per item |
| | pharmacy | 4.0% to 15% per item |
| M67 (3 to 5), RGN (2 to 4), C4 | building | 9.2%, 4.1%, 3.0% |
| | police station | 18.4%, 8.2%, 6.0% |
| Dagger, karambit, baseball bat | every theme except the pharmacy | 2.0%, 2.0%, 1.5% |
| Condensed milk (1 to 3) | building, house | 4% |
| Bread (1 to 5) | house | 16% |
| Iron pickaxe, flint and steel (worn), netherite pickaxe | workshop | 1.0%, 1.0%, 0.05% |
| Backpacks and upgrades (optional) | house | 1 in 13 (copper backpack) to 1 in 79 (stack upgrade tier 4), per item |
| Flashlight, headlamp, night vision goggles (optional) | house | 1 in 10, 1 in 16, 1 in 16 |

- **Barrels** (and dispensers/droppers, which use the barrel tables): guns, attachments and ammo are much rarer
  (building barrel: guns 0.6%, ammo 6.2%); the per-item chances above are halved, except backpacks and upgrades,
  which keep the chest chance.
- **No healing items** in the workshop, gas station and police station.
- **Guns** spawn with half a magazine (rounded up), except the minigun. Gun rarity has 7 categories (pistol, SMG,
  rifle, shotgun, machine gun, sniper, explosive) and 5 levels (Common to Legendary, each level half as likely as the
  previous one). Calibers and attachments also have levels.
- **Luck** raises the chance of every prize by 25% per level (through `quality`); chests also get extra rolls at
  high Luck. The `/loot` console command does not apply Luck.

## Tuning and regenerating

All numbers live in the block at the top of `tools/gen_loot.py`. The JSON files in `src/main/resources/data` are
generated; do not edit them by hand.

```sh
python3 -I tools/gen_loot.py             # preview: expected loot per AMC structure, Luck 0 to 3
python3 -I tools/gen_loot.py --write     # rewrite the tables and loot modifiers (runs consistency checks)
python3 -m unittest -v                   # automated tests (no server needed)
JAVA_HOME=/usr/lib/jvm/java-21-openjdk ./gradlew build -Dorg.gradle.java.installations.paths=$JAVA_HOME
                                         # builds build/libs/amctaczloot-<version>.jar (needs Java 21)
```

Tools for a local test server (RCON on 127.0.0.1:25575; password from `AMC_RCON_PASSWORD`, default `teste`):
`tools/sample_items.py` (chance per item over N containers), `tools/rcon.py` (send commands),
`tools/measure_containers.py` (containers per structure, for the preview), and the catalog extractors
`tools/tacz_catalog.py`, `tools/lr_catalog.py`, `tools/att_from_nbt.py`. Details: `CLAUDE.md`.

## Limitations

- Loot tables draw each container independently: there is no guaranteed amount per structure, only averages.
- The AMC tables are overridden by file path; if another mod also overrides them, the result depends on load order
  (this mod declares `ordering="AFTER"` for the AMC).
- A container with more stacks than slots loses the excess (vanilla behavior). For a 9-slot dispenser/dropper the
  chance is at most about 1 in 300,000; chests and barrels (27 slots) are not affected in practice.
- Item ids of the other mods are taken from their current versions; a future version that renames items may need a
  regeneration.
