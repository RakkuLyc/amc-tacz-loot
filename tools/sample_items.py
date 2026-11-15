#!/usr/bin/env python3
"""Amostra uma tabela do AMC no servidor de teste (RCON, Sorte 0) e mostra, por item, em quantos containers ele apareceu
e a quantidade média. Uso: python3 -I tools/sample_items.py <tabela, ex.: building/chest> [N] [filtro]"""
import collections, re, socket, struct, sys
table = sys.argv[1]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 1000; flt = sys.argv[3] if len(sys.argv) > 3 else ""
s = socket.create_connection(("127.0.0.1", 25575), timeout=600)
def send(k, b, r): d = struct.pack("<ii", r, k) + b.encode() + b"\0\0"; s.sendall(struct.pack("<i", len(d)) + d)
def recv():
    n = struct.unpack("<i", s.recv(4))[0]; b = b""
    while len(b) < n: b += s.recv(n - len(b))
    return b[8:-2].decode(errors="replace")
def cmd(c): send(2, c, 2); return recv()
send(3, "teste", 1); recv(); cmd("forceload add 0 0")
have = collections.Counter(); units = collections.defaultdict(list)
for _ in range(N):
    cmd("setblock 0 100 0 minecraft:air"); cmd("setblock 0 100 0 minecraft:chest")
    cmd("loot insert 0 100 0 loot abandonedmoderncity:chests/" + table)
    it = cmd("data get block 0 100 0 Items"); per = collections.Counter()
    for m in re.finditer(r'\{count: (\d+), Slot: \d+b,(.*?)id: "([a-z_:0-9]+)"\}', it, re.S):
        n, body, iid = int(m.group(1)), m.group(2), m.group(3)
        k = re.search(r'(?:ConsumableId|AmmoId|GunId|AttachmentId): "([a-z_:0-9]+)"', body)
        per[k.group(1) if k else iid] += n
    for k, v in per.items(): have[k] += 1; units[k].append(v)
for k in sorted(have, key=lambda k: -have[k]):
    if flt in k: print("%-30s em %5.1f%% dos containers | unidades por container %.1f (min %d, max %d)" % (k, 100 * have[k] / N, sum(units[k]) / len(units[k]), min(units[k]), max(units[k])))
