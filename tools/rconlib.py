#!/usr/bin/env python3
"""Minimal shared RCON client for the test server (used by rcon.py, sample_items.py and measure_containers.py).

Minecraft 1.21.1 RCON details (checked in net.minecraft.server.rcon.thread.RconClient):
- the server reads ONE packet per network read (up to 1460 bytes) and closes the connection if two packets arrive
  together, so a packet is never sent before the reply to the previous one has been read;
- replies longer than 4096 bytes arrive in several packets of up to 4096 bytes. When a piece comes with 4096 bytes,
  this client sends a packet of an unknown type (sentinel): the server only reads it after sending every piece of the
  reply and answers "Unknown request", which marks the end of the reply.
"""
import os
import socket
import struct

HOST, PORT = "127.0.0.1", 25575
# RCON password of the test server (rcon.password in run/server.properties); override with the AMC_RCON_PASSWORD
# environment variable
PASSWORD = os.environ.get("AMC_RCON_PASSWORD", "teste")
AUTH, COMMAND, SENTINEL = 3, 2, 0       # packet types; 0 is not handled by the server (becomes "Unknown request")
CHUNK = 4096                            # max size of one reply piece (RconClient.sendCmdResponse)


class Rcon:
    def __init__(self, password=PASSWORD, host=HOST, port=PORT, timeout=600):
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self._send(1, AUTH, password)
        if self._read()[0] == -1:
            raise SystemExit("RCON: password rejected")

    def _send(self, rid, kind, body):
        data = struct.pack("<ii", rid, kind) + body.encode("utf-8") + b"\x00\x00"
        self.sock.sendall(struct.pack("<i", len(data)) + data)

    def _exact(self, n):
        """Reads exactly n bytes (recv may return fewer than asked)."""
        buf = b""
        while len(buf) < n:
            part = self.sock.recv(n - len(buf))
            if not part:
                raise ConnectionError("RCON: connection closed by the server")
            buf += part
        return buf

    def _read(self):
        """One packet: (id, body as bytes)."""
        n = struct.unpack("<i", self._exact(4))[0]
        buf = self._exact(n)
        rid = struct.unpack("<i", buf[:4])[0]
        return rid, buf[8:-2]

    def cmd(self, command):
        """Runs a command and returns the whole reply (joins the pieces of long replies)."""
        self._send(2, COMMAND, command)
        rid, body = self._read()
        parts = [body]
        if len(body) >= CHUNK:                       # there may be more pieces: mark the end with the sentinel
            self._send(3, SENTINEL, "")
            while True:
                rid, body = self._read()
                if rid == 3:
                    break
                parts.append(body)
        return b"".join(parts).decode("utf-8", errors="replace")

    def close(self):
        self.sock.close()
