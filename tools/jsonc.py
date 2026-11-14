#!/usr/bin/env python3
"""Leitor de JSON tolerante (comentários // e /* */, vírgula sobrando), como o dos mods."""
import json, re


def jsonc(text):
    """JSON tolerante, como o do TACZ: comentários // e /* */ e vírgula sobrando (respeita strings)."""
    out, i, n, instr = [], 0, len(text), False
    while i < n:
        c = text[i]
        if instr:
            out.append(c)
            if c == "\\":
                out.append(text[i + 1]); i += 1
            elif c == '"':
                instr = False
        elif c == '"':
            instr = True; out.append(c)
        elif text.startswith("//", i):
            while i < n and text[i] != "\n": i += 1
            continue
        elif text.startswith("/*", i):
            i = text.index("*/", i) + 2
            continue
        else:
            out.append(c)
        i += 1
    return json.loads(re.sub(r",(\s*[}\]])", r"\1", "".join(out)))
