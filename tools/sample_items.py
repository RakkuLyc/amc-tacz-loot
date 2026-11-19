#!/usr/bin/env python3
"""Samples an AMC table on the test server (RCON, Luck 0: the console /loot does not apply Luck) and shows, per item,
in how many containers it appeared (exact count and %) and the units per container.

Usage: python3 -I tools/sample_items.py <table, e.g. building/chest> [N] [filter] [--json out.json] [--x X]
  filter      only show the keys that contain this text
  --json      write the raw counts (to compare samples later)
  --x X       X coordinate of the test chest (default 0)

Key of each item: the TACZ/LesRaisins internal ID when there is one (GunId, AmmoId, ...), otherwise the item id; the
TACZ ammo box gets its level (tacz:ammo_box#L0 iron, #L1 gold, #L2 diamond). For guns it also counts the raw text of
GunCurrentAmmoCount: TACZ only reads the magazine if the number is an INTEGER ("9"); "9b" would be a byte (the 1.0.0 bug).
"""
import argparse
import collections
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # with -I the script folder is not on sys.path by itself
from rconlib import Rcon

CUSTOM_ID = re.compile(r'(?:ConsumableId|ThrowableId|MeleeWeaponId|AmmoId|GunId|AttachmentId): "([a-z_:0-9]+)"')


def split_items(txt):
    """Splits the reply `... [{...}, {...}]` into the top-level items (counts braces, respects quoted text)."""
    start_list = txt.find("[")
    if start_list < 0:
        return []
    res, depth, start, in_str, esc = [], 0, None, False, False
    for j in range(start_list + 1, len(txt)):
        c = txt[j]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "{":
            if depth == 0:
                start = j
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                res.append(txt[start:j + 1])
    return res


def item_key(item):
    """(key, units, item id) of one item from the `data get` reply."""
    count = int(re.match(r"\{count: (\d+)", item).group(1))
    iid = re.search(r'id: "([a-z_:0-9]+)"\}$', item).group(1)
    m = CUSTOM_ID.search(item)
    key = m.group(1) if m else iid
    if iid == "tacz:ammo_box":
        lv = re.search(r"Level: (\w+)", item)
        key += "#L" + (lv.group(1) if lv else "none")
    return key, count, iid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("table"); ap.add_argument("n", nargs="?", type=int, default=1000); ap.add_argument("filter", nargs="?", default="")
    ap.add_argument("--json"); ap.add_argument("--x", type=int, default=0)
    a = ap.parse_args()
    r = Rcon()
    pos = "%d 100 0" % a.x
    r.cmd("forceload add %d 0" % a.x)
    have, units, umin, umax = collections.Counter(), collections.Counter(), {}, {}
    gun_ammo_raw = collections.Counter()
    errors = 0
    t0 = time.time()
    for _ in range(a.n):
        r.cmd("setblock %s minecraft:air" % pos); r.cmd("setblock %s minecraft:chest" % pos)
        resp = r.cmd("loot insert %s loot abandonedmoderncity:chests/%s" % (pos, a.table))
        if "dropped" not in resp.lower():
            errors += 1
            if errors <= 3: print("unexpected reply:", resp)
        per = collections.Counter()
        for item in split_items(r.cmd("data get block %s Items" % pos)):
            key, n, iid = item_key(item)
            per[key] += n
            if iid == "tacz:modern_kinetic_gun":
                raw = re.search(r"GunCurrentAmmoCount: (\w+)", item)
                gun_ammo_raw[key + "=" + (raw.group(1) if raw else "none")] += 1
        for key, n in per.items():
            have[key] += 1; units[key] += n
            umin[key] = min(umin.get(key, n), n); umax[key] = max(umax.get(key, n), n)
    r.close()
    dt = time.time() - t0
    print("%s  N=%d  %.0f s  errors %d" % (a.table, a.n, dt, errors))
    for k in sorted(have, key=lambda k: -have[k]):
        if a.filter in k:
            print("%-34s in %6d containers (%7.3f%%) | units per container %.1f (min %d, max %d)"
                  % (k, have[k], 100 * have[k] / a.n, units[k] / have[k], umin[k], umax[k]))
    if a.json:
        out = dict(table=a.table, N=a.n, seconds=round(dt, 1), errors=errors,
                   keys={k: dict(have=have[k], units=units[k], min=umin[k], max=umax[k]) for k in sorted(have)},
                   gun_ammo_raw=dict(sorted(gun_ammo_raw.items())))
        json.dump(out, open(a.json, "w"), indent=1)


main()
