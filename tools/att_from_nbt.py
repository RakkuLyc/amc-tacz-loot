#!/usr/bin/env python3
"""Gera docs/attachments_rarity.json (e docs/ammo_rarity.json, de tacz_ammo.nbt) a partir das estruturas .nbt que o usuário montou (baús com os attachments).
Regra do usuário (17 Nov 2026): o nível é a cor do concreto no mesmo x/z, ACIMA do baú (cinza-claro Comum, lima Incomum, azul-claro Raro, magenta Épico,
amarelo Lendário, laranja Mítico); baú sem bloco em cima = sem raridade definida. Uso: python3 -I tools/att_from_nbt.py <pasta das structures>"""
import glob, gzip, json, os, struct, sys

COL = {"light_gray_concrete": "Comum", "lime_concrete": "Incomum", "light_blue_concrete": "Raro", "magenta_concrete": "Épico",
       "yellow_concrete": "Lendário", "orange_concrete": "Mítico"}


def parse(path):
    b = gzip.open(path).read(); pos = [0]
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
        if f.endswith("tacz_ammo.nbt"): continue          # munição: ammo_levels()
        d = parse(f); pal = [p["Name"].replace("minecraft:", "") for p in d["palette"]]
        grid = {tuple(b["pos"]): pal[b["state"]] for b in d["blocks"]}; fam = os.path.basename(f)[5:-4]
        for b in d["blocks"]:
            if "nbt" not in b: continue
            x, y, z = b["pos"]; lv = None
            for yy in range(y + 1, d["size"][1]):
                if grid.get((x, yy, z)) in COL: lv = COL[grid[(x, yy, z)]]
            for it in b["nbt"].get("Items", []):
                a = it["components"]["minecraft:custom_data"]["AttachmentId"].split(":")[1]
                res[a] = dict(id=a, family=fam, level=lv or "Sem raridade")      # duplicata (ex.: stock_m4ss) conta uma vez
    out = sorted(res.values(), key=lambda r: (r["family"], r["id"]))
    json.dump(out, open("docs/attachments_rarity.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    cnt = {}
    for r in out: cnt[r["level"]] = cnt.get(r["level"], 0) + 1
    print(len(out), "attachments:", cnt)


def ammo_levels(folder):
    """Munição (tacz_ammo.nbt, 17 Nov 2026): mesma regra da cor do concreto; a quantidade dentro do baú é só o tamanho cheio da pilha (não é regra)."""
    d = parse(os.path.join(folder, "tacz_ammo.nbt")); pal = [p["Name"].replace("minecraft:", "") for p in d["palette"]]
    grid = {tuple(b["pos"]): pal[b["state"]] for b in d["blocks"]}; res = []
    for b in d["blocks"]:
        if "nbt" not in b: continue
        x, y, z = b["pos"]; lv = None
        for yy in range(y + 1, d["size"][1]):
            if grid.get((x, yy, z)) in COL: lv = COL[grid[(x, yy, z)]]
        for it in b["nbt"].get("Items", []):
            res.append(dict(id=it["components"]["minecraft:custom_data"]["AmmoId"].split(":")[1], level=lv or "Sem raridade"))
    res.sort(key=lambda r: r["id"]); json.dump(res, open("docs/ammo_rarity.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(res), "calibres")


if __name__ == "__main__":
    main(sys.argv[1]); ammo_levels(sys.argv[1])
