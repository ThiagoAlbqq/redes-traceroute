"""Simulador deterministico de rede para o Projeto 1 - Traceroute.

Este modulo fornece objetos com a mesma interface minima usada pela funcao traceroute
(set_ttl, sendto, recv_select e recvfrom), mas sem acessar a rede real e sem exigir root.
Cada envio gera uma resposta ICMP sintetica de acordo com o cenario configurado.
"""

import socket
from collections import defaultdict, deque


IP_LOCAL = "192.0.2.10"


def _ipv4_bytes(ip: str) -> bytes:
    return socket.inet_aton(ip)


def construir_ipv4(src: str, dst: str, protocolo: int, payload: bytes,
                    ttl: int = 64, ihl: int = 5, identificacao: int = 0x1234,
                    flags: int = 0, offset: int = 0, tos: int = 0,
                    opcoes: bytes = b"") -> bytes:
    """Constroi um pacote IPv4 simples, suficiente para os testes do projeto."""
    if ihl < 5:
        raise ValueError("IHL deve ser pelo menos 5")
    tamanho_opcoes = (ihl - 5) * 4
    if len(opcoes) != tamanho_opcoes:
        raise ValueError("O tamanho de opcoes deve corresponder ao IHL")

    versao_ihl = (4 << 4) | ihl
    total = ihl * 4 + len(payload)
    flags_offset = ((flags & 0x7) << 13) | (offset & 0x1FFF)
    cab = bytes([versao_ihl, tos])
    cab += total.to_bytes(2, "big")
    cab += identificacao.to_bytes(2, "big")
    cab += flags_offset.to_bytes(2, "big")
    cab += bytes([ttl, protocolo])
    cab += (0).to_bytes(2, "big")
    cab += _ipv4_bytes(src)
    cab += _ipv4_bytes(dst)
    cab += opcoes
    return cab + payload


def construir_udp(src_port: int, dst_port: int, payload: bytes = b"") -> bytes:
    tamanho = 8 + len(payload)
    return (
        src_port.to_bytes(2, "big")
        + dst_port.to_bytes(2, "big")
        + tamanho.to_bytes(2, "big")
        + (0).to_bytes(2, "big")
        + payload
    )


def construir_icmp(tipo: int, codigo: int, payload: bytes = b"") -> bytes:
    return bytes([tipo, codigo, 0, 0, 0, 0, 0, 0]) + payload


def resposta_icmp(respondedor: str, destino: str, ttl_sonda: int,
                   porta_destino: int, alcancou_destino: bool) -> bytes:
    """Gera uma resposta ICMP com a sonda UDP original embutida no payload."""
    udp_original = construir_udp(40000, porta_destino, b"teste")
    ip_original = construir_ipv4(
        IP_LOCAL, destino, socket.IPPROTO_UDP, udp_original, ttl=ttl_sonda
    )
    if alcancou_destino:
        # Destino inalcançavel / porta inalcançavel.
        icmp = construir_icmp(3, 3, ip_original)
    else:
        # Tempo excedido / TTL expirado em transito.
        icmp = construir_icmp(11, 0, ip_original)
    return construir_ipv4(
        respondedor, IP_LOCAL, socket.IPPROTO_ICMP, icmp, ttl=64
    )


class RedeSimulada:
    """Representa uma topologia por niveis de TTL.

    `saltos` e uma lista em que cada elemento corresponde a um TTL. Cada nivel contem uma
    lista de respostas possiveis para sondas sucessivas. Use None para representar perda de
    pacote/ausencia de resposta. Quando a resposta e o proprio destino, o simulador gera
    ICMP tipo 3, codigo 3; para os demais roteadores, gera ICMP tipo 11, codigo 0.
    """

    def __init__(self, destino: str, saltos: list[list[str | None]]):
        self.destino = destino
        self.saltos = saltos
        self.fila = deque()
        self.contador_por_ttl = defaultdict(int)
        self.ttl_atual = 1

    def sockets(self):
        return SocketEnvioSimulado(self), SocketRecepcaoSimulado(self)

    def registrar_envio(self, payload: bytes, endereco: tuple[str, int]):
        destino, porta = endereco
        ttl = self.ttl_atual
        if destino != self.destino or ttl < 1 or ttl > len(self.saltos):
            return len(payload)

        respostas = self.saltos[ttl - 1]
        if not respostas:
            return len(payload)

        indice = self.contador_por_ttl[ttl]
        self.contador_por_ttl[ttl] += 1
        respondedor = respostas[indice % len(respostas)]
        if respondedor is None:
            return len(payload)

        pacote = resposta_icmp(
            respondedor=respondedor,
            destino=self.destino,
            ttl_sonda=ttl,
            porta_destino=porta,
            alcancou_destino=(respondedor == self.destino),
        )
        self.fila.append((pacote, (respondedor, 0)))
        return len(payload)


class SocketEnvioSimulado:
    def __init__(self, rede: RedeSimulada):
        self.rede = rede

    def set_ttl(self, ttl: int):
        self.rede.ttl_atual = ttl

    def sendto(self, b: bytes, address: tuple[str, int]) -> int:
        return self.rede.registrar_envio(b, address)


class SocketRecepcaoSimulado:
    def __init__(self, rede: RedeSimulada):
        self.rede = rede

    def recv_select(self) -> bool:
        return bool(self.rede.fila)

    def recvfrom(self):
        if not self.rede.fila:
            raise RuntimeError("recvfrom chamado sem pacote disponivel")
        return self.rede.fila.popleft()
