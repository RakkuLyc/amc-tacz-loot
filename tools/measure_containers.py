#!/usr/bin/env python3
"""Mede quantos containers de cada tipo cada estrutura do AMC tem (-> docs/containers.json).

Com o servidor de teste rodando (RCON 25575): gera cada estrutura do AMC numa célula de 400x400 blocos com
`/amcs spawn`, salva o mundo e lê os arquivos de região contando os block entities com LootTable, por tema e tipo.
Uso: python3 -I tools/measure_containers.py <index.txt do AMC> <pasta do mundo (run/world)> [nomes,separados,por,vírgula [deslocamento]]"""
import collections, glob, json, socket, struct, sys, zlib

CATS = ["house", "pharmacy", "workshop", "gas_station", "building", "police_station", "special"]


def rcon(cmds):
    s = socket.create_connection(("127.0.0.1", 25575), timeout=120)

    def send(kind, body, rid):
        d = struct.pack("<ii", rid, kind) + body.encode() + b"\0\0"
        s.sendall(struct.pack("<i", len(d)) + d)

    def recv():
        n = struct.unpack("<i", s.recv(4))[0]; b = b""
        while len(b) < n: b += s.recv(n - len(b))
        return b[8:-2].decode(errors="replace")
    send(3, "teste", 1); recv()
    out = []
    for c in cmds:
        send(2, c, 2); out.append(recv())
    return out


def category(type_):
    # mesma regra do AMC: Structures.CATEGORIES, por início do tipo ("houses" -> house). Desde 16 Nov 2026 os prédios têm categoria por altura:
    # "buildings_small" -> building_small (idem medium, large, immense).
    if type_.startswith("buildings_"): return "building_" + type_[len("buildings_"):]
    for k in CATS:
        if type_.startswith(k) or type_.startswith(k + "s"):
            return k
    raise SystemExit("tipo sem categoria: " + type_)


def nbt(b, p, t):
    u = struct.unpack
    if t == 1: return b[p], p + 1
    if t == 2: return u(">h", b[p:p + 2])[0], p + 2
    if t == 3: return u(">i", b[p:p + 4])[0], p + 4
    if t == 4: return u(">q", b[p:p + 8])[0], p + 8
    if t == 5: return None, p + 4
    if t == 6: return None, p + 8
    if t == 7: return None, p + 4 + u(">i", b[p:p + 4])[0]
    if t == 8:
        n = u(">H", b[p:p + 2])[0]; return b[p + 2:p + 2 + n].decode("utf-8", "replace"), p + 2 + n
    if t == 9:
        it = b[p]; n = u(">i", b[p + 1:p + 5])[0]; p += 5; out = []
        for _ in range(n):
            v, p = nbt(b, p, it); out.append(v)
        return out, p
    if t == 10:
        d = {}
        while True:
            tt = b[p]; p += 1
            if tt == 0: return d, p
            n = u(">H", b[p:p + 2])[0]; k = b[p + 2:p + 2 + n].decode(); p += 2 + n
            d[k], p = nbt(b, p, tt)
    if t == 11: return None, p + 4 + 4 * u(">i", b[p:p + 4])[0]
    if t == 12: return None, p + 4 + 8 * u(">i", b[p:p + 4])[0]
    raise ValueError(t)


def block_entities(world):
    for f in glob.glob(world + "/region/*.mca"):
        b = open(f, "rb").read()
        if len(b) < 8192: continue  # região vazia (mundo novo)
        for i in range(1024):
            off = struct.unpack(">I", b"\0" + b[i * 4:i * 4 + 3])[0]
            if not off: continue
            pos = off * 4096; ln = struct.unpack(">I", b[pos:pos + 4])[0]
            data = zlib.decompress(b[pos + 5:pos + 4 + ln])
            n = struct.unpack(">H", data[1:3])[0]
            root, _ = nbt(data, 3 + n, 10)
            yield from root.get("block_entities", [])


def main(index, world, only=None, offset=0):
    import re
    items = [l.rstrip("\n").split("|") for l in open(index, encoding="utf-8") if l.strip() and not l.startswith("#")]
    names = [(category(i[0]), i[1]) for i in items if only is None or i[1] in only]
    cmds = ["execute in minecraft:overworld positioned %d 80 %d rotated 0 0 run amcs spawn %s %s"
            % (offset + 400 * (n % 8) + 200, offset + 400 * (n // 8) + 200, cat, name) for n, (cat, name) in enumerate(names)]
    boxes = {}
    for (cat, name), r in zip(names, rcon(cmds)):
        m = re.search(r"box (-?\d+),(-?\d+) \.\. (-?\d+),(-?\d+).*?(\d+) containers with loot", r)
        if not m:
            print("FALHOU", name, r); continue
        boxes[name] = tuple(int(g) for g in m.groups())
    rcon(["save-all flush"])
    res = {n: collections.Counter() for n in boxes}
    theme = {}
    for be in block_entities(world):
        lt = be.get("LootTable")
        if not lt or not lt.startswith("abandonedmoderncity:chests/"): continue
        for name, (x1, z1, x2, z2, _) in boxes.items():
            if x1 <= be["x"] <= x2 and z1 <= be["z"] <= z2:
                th, tier = lt.split("chests/")[1].split("/")
                theme[name] = th; res[name][tier] += 1
                break
    out = {}
    for n, c in sorted(res.items()):
        total = sum(c.values())
        ok = "ok" if total == boxes[n][4] else "DIFERENTE do informado (%d)" % boxes[n][4]
        out[n] = {"theme": theme.get(n), "tiers": dict(sorted(c.items())), "total": total}
        print("%-34s %-14s %4d %s  %s" % (n, theme.get(n), total, dict(sorted(c.items())), ok))
    if only is not None:  # repetição de algumas estruturas: junta ao resultado anterior
        old = json.load(open("docs/containers.json")); old.update(out); out = dict(sorted(old.items()))
    json.dump(out, open("docs/containers.json", "w"), indent=1)


main(sys.argv[1], sys.argv[2], set(sys.argv[3].split(",")) if len(sys.argv) > 3 else None,
     int(sys.argv[4]) if len(sys.argv) > 4 else 0)
