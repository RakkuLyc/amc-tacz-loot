#!/usr/bin/env python3
"""Amostra uma tabela do AMC no servidor de teste (RCON) e compara a média observada com a prévia do gerador (Sorte 0:
o /loot do console não aplica Sorte). Uso: python3 -I tools/sample_loot.py <tema> <tier> [N]"""
import os, re, socket, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_loot

theme, tier = sys.argv[1], sys.argv[2]; N = int(sys.argv[3]) if len(sys.argv) > 3 else 400
s = socket.create_connection(("127.0.0.1", 25575), timeout=120)

def send(kind, body, rid):
    d = struct.pack("<ii", rid, kind) + body.encode() + b"\0\0"; s.sendall(struct.pack("<i", len(d)) + d)

def recv():
    n = struct.unpack("<i", s.recv(4))[0]; b = b""
    while len(b) < n: b += s.recv(n - len(b))
    return b[8:-2].decode(errors="replace")

def cmd(c):
    send(2, c, 2); return recv()

send(3, "teste", 1); recv()
cmd("forceload add 0 0")
tot = dict(gun=0, ammo=0, att=0, lr=0, fa=0); anyitem = 0; errs = 0
for _ in range(N):
    cmd("setblock 0 100 0 minecraft:air"); cmd("setblock 0 100 0 minecraft:chest")
    r = cmd("loot insert 0 100 0 loot abandonedmoderncity:chests/%s/%s" % (theme, tier))
    if "Dropped" not in r: errs += 1; print("ERRO:", r); break
    items = cmd("data get block 0 100 0 Items")
    got = 0
    # cada item: {count: N, Slot: Xb, [components: {... aninhado ...},] id: "ns:nome"}
    for m in re.finditer(r'count: (\d+), Slot: \d+b,.*?\bid: "([a-z_:0-9]+)"\}', items, re.S):
        n, i = int(m.group(1)), m.group(2)
        if i == "tacz:modern_kinetic_gun": tot["gun"] += 1; got = 1
        elif i == "tacz:ammo": tot["ammo"] += 1; got = 1
        elif i == "tacz:attachment": tot["att"] += 1; got = 1
        elif i == "lrtactical:consumable": tot["lr"] += n; got = 1
        elif i.startswith("firstaid:"): tot["fa"] += n; got = 1
    anyitem += got
exp = gen_loot.expected(theme, tier, 0)
print("%s/%s  N=%d  chance de ter algo do mod: %.0f%%" % (theme, tier, N, 100 * anyitem / N))
for k in tot: print("  %-5s observado %.3f   esperado %.3f" % (k, tot[k] / N, exp[k]))
