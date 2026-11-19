#!/usr/bin/env python3
"""Cliente RCON mínimo e único para o servidor de teste (usado por rcon.py, sample_items.py e measure_containers.py).

Detalhes do RCON do Minecraft 1.21.1 (conferidos em net.minecraft.server.rcon.thread.RconClient):
- o servidor lê UM pacote por leitura de rede (até 1460 bytes) e fecha a conexão se dois pacotes chegarem juntos,
  por isso nunca se envia um pacote antes de ler a resposta do anterior;
- respostas maiores que 4096 bytes chegam em vários pacotes de até 4096 bytes. Quando um pedaço vem com 4096 bytes,
  este cliente envia um pacote de tipo desconhecido (sentinela): o servidor só o lê depois de mandar todos os pedaços
  da resposta e responde "Unknown request", o que marca o fim da resposta.
"""
import os
import socket
import struct

HOST, PORT = "127.0.0.1", 25575
# senha do RCON do servidor de teste (rcon.password em run/server.properties); troque pela variável de ambiente AMC_RCON_PASSWORD
PASSWORD = os.environ.get("AMC_RCON_PASSWORD", "teste")
AUTH, COMMAND, SENTINEL = 3, 2, 0       # tipos de pacote; o 0 não é tratado pelo servidor (vira "Unknown request")
CHUNK = 4096                            # tamanho máximo de um pedaço de resposta (RconClient.sendCmdResponse)


class Rcon:
    def __init__(self, password=PASSWORD, host=HOST, port=PORT, timeout=600):
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self._send(1, AUTH, password)
        if self._read()[0] == -1:
            raise SystemExit("RCON: senha recusada")

    def _send(self, rid, kind, body):
        data = struct.pack("<ii", rid, kind) + body.encode("utf-8") + b"\x00\x00"
        self.sock.sendall(struct.pack("<i", len(data)) + data)

    def _exact(self, n):
        """Lê exatamente n bytes (recv pode devolver menos que o pedido)."""
        buf = b""
        while len(buf) < n:
            part = self.sock.recv(n - len(buf))
            if not part:
                raise ConnectionError("RCON: conexão fechada pelo servidor")
            buf += part
        return buf

    def _read(self):
        """Um pacote: (id, corpo em bytes)."""
        n = struct.unpack("<i", self._exact(4))[0]
        buf = self._exact(n)
        rid = struct.unpack("<i", buf[:4])[0]
        return rid, buf[8:-2]

    def cmd(self, command):
        """Executa um comando e devolve a resposta inteira (junta os pedaços de respostas longas)."""
        self._send(2, COMMAND, command)
        rid, body = self._read()
        parts = [body]
        if len(body) >= CHUNK:                       # pode haver mais pedaços: marca o fim com o sentinela
            self._send(3, SENTINEL, "")
            while True:
                rid, body = self._read()
                if rid == 3:
                    break
                parts.append(body)
        return b"".join(parts).decode("utf-8", errors="replace")

    def close(self):
        self.sock.close()
