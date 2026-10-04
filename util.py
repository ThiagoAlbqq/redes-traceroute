import argparse
import select
import socket
import typing
import sys
import platform

# === Nao modificar ===

# SELECT_TIMEOUT indica por quantos segundos a chamada select pode bloquear quando nenhum
# pacote e recebido. Um valor menor torna mais provavel que o programa desista antes de uma
# resposta chegar; um valor maior deixa as sondas sem resposta mais lentas. Na pratica,
# 2 segundos oferece um bom equilibrio. Os testes locais nao dependem deste valor; ele afeta
# apenas execucoes em redes reais.
SELECT_TIMEOUT = 2

IPPROTO_ICMP = socket.IPPROTO_ICMP
IPPROTO_UDP = socket.IPPROTO_UDP


def ntohl(x):
    return socket.ntohl(x)


def htonl(x):
    return socket.htonl(x)


def htons(x):
    return socket.htons(x)


def ntohs(x):
    return socket.ntohs(x)


def inet_aton(x):
    return socket.inet_aton(x)


def inet_ntoa(x):
    return socket.inet_ntoa(x)


def inet_pton(x, y):
    return socket.inet_pton(x, y)


def inet_ntop(x, y):
    return socket.inet_ntop(x, y)


def gethostbyname(host: str):
    return socket.gethostbyname(host)


class Socket:
    __sock: socket.socket

    # Cria um socket UDP usado para enviar as sondas do traceroute. O codigo inicial
    # chama este metodo para voce.
    @classmethod
    def make_udp(cls):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                             socket.IPPROTO_UDP)
        return cls(sock)

    # Cria um socket ICMP usado para receber respostas ICMP. O codigo inicial chama
    # este metodo para voce.
    @classmethod
    def make_icmp(cls):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW,
                                 socket.IPPROTO_ICMP)
        except PermissionError:
            if platform.system() != "Darwin":
                print("PermissionError: execute o programa como administrador/root.")
                sys.exit(1)

            # No macOS e possivel criar um socket ICMP sem privilegios. O socket raw e
            # preferivel por ser menos fragil e mais portavel, mas usamos esta alternativa
            # quando a criacao do socket raw falha.
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                 socket.IPPROTO_ICMP)
        return cls(sock)

    def __init__(self, sock: socket.socket):
        self.__sock = sock

    # Chamado apenas no socket UDP. Altera o TTL de todos os pacotes enviados
    # posteriormente por este socket.
    def set_ttl(self, ttl: int):
        return self.__sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)

    # Chamado apenas no socket UDP. Envia um pacote UDP para `address`.
    # `address` e uma tupla com a representacao textual de um endereco IPv4 e a porta
    # de destino. O payload do pacote UDP e `b`. O cabecalho UDP e criado pela funcao
    # sendto com base nas informacoes fornecidas.
    #
    # Referencia: https://docs.python.org/3/library/socket.html#socket.socket.sendto
    def sendto(self, b: bytes, address: typing.Tuple[str, int]) -> int:
        return self.__sock.sendto(b, address)

    # Chamado apenas no socket ICMP. Recebe um pacote do socket.
    # Retorna um objeto `bytes` contendo o pacote completo, incluindo o cabecalho IP,
    # e tambem o endereco de quem enviou o pacote.
    #
    # Referencia: https://docs.python.org/3/library/socket.html#socket.socket.recvfrom
    def recvfrom(self) -> typing.Tuple[bytes, typing.Tuple[str, int]]:
        return self.__sock.recvfrom(4096)

    # Chamado apenas no socket ICMP. Bloqueia ate que haja um pacote disponivel para
    # recvfrom(), ou ate SELECT_TIMEOUT expirar. Retorna True se houver pacote disponivel.
    #
    # Referencia: https://docs.python.org/3/library/select.html#select.select
    def recv_select(self) -> bool:
        rlist, _, _ = select.select([self.__sock], [], [], SELECT_TIMEOUT)
        return rlist != []


def print_result(routers: list[str], ttl: int):
    if len(routers) == 0:
        print(f"{ttl: >2}: *")
        return

    for i, router in enumerate(routers):
        if i == 0:
            preamble = f"{ttl: >2}:"
        else:
            preamble = "   "

        try:
            hostname, _, _ = socket.gethostbyaddr(router)
            print(f"{preamble} {hostname} ({router})")
        except socket.herror:
            print(f"{preamble} {router}")


def parse_args():
    parser = argparse.ArgumentParser(prog='Traceroute')
    parser.add_argument('host')
    return parser.parse_args()
