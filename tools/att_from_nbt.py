#!/usr/bin/env python3
"""Builds docs/attachments_rarity.json (and docs/ammo_rarity.json, from tacz_ammo.nbt) from the .nbt structures the user
built (chests holding the attachments).
User's rule (17 Nov 2026): the level is the concrete color at the same x/z, ABOVE the chest (light gray Common, lime
Uncommon, light blue Rare, magenta Epic, yellow Legendary, orange Mythic); chest with nothing above = unrated.
The level names are written in Portuguese (Comum, Incomum, Raro, Épico, Lendário, Mítico, Sem raridade) because
tools/gen_loot.py reads them. Usage: python3 -I tools/att_from_nbt.py <structures folder>"""
import glob, gzip, json, os, struct, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # project root: writes into docs/ from any folder

MAX_NBT = 256 << 20     # decompression limit (256 MB): a normal structure has a few KB
COL = {"light_gray_concrete": "Comum", "lime_concrete": "Incomum", "light_blue_concrete": "Raro", "magenta_concrete": "Épico",
       "yellow_concrete": "Lendário", "orange_concrete": "Mítico"}


def parse(path):
    with gzip.open(path) as f: b = f.read(MAX_NBT + 1)
    if len(b) > MAX_NBT: sys.exit("%s: larger than %d MB uncompressed (suspicious file)" % (path, MAX_NBT >> 20))
    pos = [0]
    def r(fmt):
        n = struct.calcsize(fmt); v = struct.unpack_from(fmt, b, pos[0]); pos[0] += n; return v[0]
    def s():
        n = r(">H"); v = b[pos[0]:pos[0] + n].decode("utf-8", "replace"); pos[0] += n; return v
    def pl(t):
        if t in (1, 2, 3, 4, 5, 6): return r(">" + {1: "b", 2: "h", 3: "i", 4: "q", 5: "f", 6: "d"}[t])
        if t == 7: n = r(">i"); pos[0] += n; return None
        if t == 8: return s()
        if t == 9: it = r(">b"); n = r(">i"); return [pl(it) for _ in range(n)]
        if t == 10:
            d = {}
            while True:
                tt = r(">b")
                if tt == 0: return d
                k = s(); d[k] = pl(tt)
        if t == 11: n = r(">i"); return [r(">i") for _ in range(n)]
        if t == 12: n = r(">i"); return [r(">q") for _ in range(n)]
        raise ValueError(t)
    t = r(">b"); s(); return pl(t)


def main(folder):
    res = {}
    for f in sorted(glob.glob(os.path.join(folder, "tacz_*.nbt"))):
        if f.endswith("tacz_ammo.nbt"): continue          # ammo: ammo_levels()
        d = parse(f); pal = [p["Name"].replace("minecraft:", "") for p in d["palette"]]
        grid = {tuple(b["pos"]): pal[b["state"]] for b in d["blocks"]}; fam = os.path.basename(f)[5:-4]
        for b in d["blocks"]:
            if "nbt" not in b: continue
            x, y, z = b["pos"]; lv = None
            for yy in range(y + 1, d["size"][1]):
                if grid.get((x, yy, z)) in COL: lv = COL[grid[(x, yy, z)]]
            for it in b["nbt"].get("Items", []):
                a = it["components"]["minecraft:custom_data"]["AttachmentId"].split(":")[1]
                res[a] = dict(id=a, family=fam, level=lv or "Sem raridade")      # a duplicate (e.g. stock_m4ss) counts once
    out = sorted(res.values(), key=lambda r: (r["family"], r["id"]))
    json.dump(out, open(os.path.join(ROOT, "docs/attachments_rarity.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    cnt = {}
    for r in out: cnt[r["level"]] = cnt.get(r["level"], 0) + 1
    print(len(out), "attachments:", cnt)


def ammo_levels(folder):
    """Ammo (tacz_ammo.nbt, 17 Nov 2026): same concrete-color rule; the amount inside the chest is just the full stack
    size (not a rule)."""
    d = parse(os.path.join(folder, "tacz_ammo.nbt")); pal = [p["Name"].replace("minecraft:", "") for p in d["palette"]]
    grid = {tuple(b["pos"]): pal[b["state"]] for b in d["blocks"]}; res = []
    for b in d["blocks"]:
        if "nbt" not in b: continue
        x, y, z = b["pos"]; lv = None
        for yy in range(y + 1, d["size"][1]):
            if grid.get((x, yy, z)) in COL: lv = COL[grid[(x, yy, z)]]
        for it in b["nbt"].get("Items", []):
            res.append(dict(id=it["components"]["minecraft:custom_data"]["AmmoId"].split(":")[1], level=lv or "Sem raridade"))
    res.sort(key=lambda r: r["id"]); json.dump(res, open(os.path.join(ROOT, "docs/ammo_rarity.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(res), "calibers")


if __name__ == "__main__":
    # check the folder BEFORE writing: with the wrong folder the script would write empty lists over docs/ (it happened
    # during the 18 Nov 2026 review)
    att_files = [f for f in glob.glob(os.path.join(sys.argv[1], "tacz_*.nbt")) if not f.endswith("tacz_ammo.nbt")]
    if not att_files or not os.path.isfile(os.path.join(sys.argv[1], "tacz_ammo.nbt")):
        sys.exit("folder without tacz_ammo.nbt or the tacz_<family>.nbt structures: %s (nothing written)" % sys.argv[1])
    main(sys.argv[1]); ammo_levels(sys.argv[1])
