#!/usr/bin/env python3
"""Sends commands to the test server over RCON and prints each reply.
Usage: python3 -I tools/rcon.py "command 1" "command 2" ..."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # with -I the script folder is not on sys.path by itself
from rconlib import Rcon


def main():
    r = Rcon(timeout=60)
    for cmd in sys.argv[1:]:
        print(">", cmd)
        print(r.cmd(cmd))
    r.close()


main()
