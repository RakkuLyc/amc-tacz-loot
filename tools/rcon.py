#!/usr/bin/env python3
"""Envia comandos ao servidor de teste por RCON e imprime a resposta de cada um.
Uso: python3 -I tools/rcon.py "comando 1" "comando 2" ..."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # com -I a pasta do script não entra no sys.path sozinha
from rconlib import Rcon


def main():
    r = Rcon(timeout=60)
    for cmd in sys.argv[1:]:
        print(">", cmd)
        print(r.cmd(cmd))
    r.close()


main()
