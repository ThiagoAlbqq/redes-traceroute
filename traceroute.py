import util

# Seu programa deve enviar TTLs no intervalo [1, TRACEROUTE_MAX_TTL], inclusive.
# Tecnicamente, o IPv4 permite TTLs de ate 255, mas, na pratica, isso e excessivo.
# A maioria das implementacoes de traceroute limita o valor a aproximadamente 30.
# Os testes fornecidos assumem que este valor nao sera alterado.
TRACEROUTE_MAX_TTL = 30

# A Cisco popularizou o uso das portas UDP no intervalo [33434, 33464] para traceroute.
# Embora isso nao seja um padrao formal, alguns roteadores na Internet respondem de forma
# mais consistente com mensagens ICMP de tempo excedido para pacotes UDP enviados a essas
# portas. Voce pode usar outra porta, mas este valor e adequado para o projeto.
TRACEROUTE_PORT_NUMBER = 33434

# Pacotes podem ser descartados na Internet. PROBE_ATTEMPT_COUNT e o numero maximo de
# sondas que a funcao traceroute deve enviar para um mesmo TTL antes de seguir adiante.
PROBE_ATTEMPT_COUNT = 3


class IPv4:
    # Cada membro abaixo corresponde a um campo do cabecalho IPv4. Os campos aparecem
    # na mesma ordem em que estao no pacote. Todos devem ser armazenados na ordem de
    # bytes do host.
    #
    # Modifique apenas o metodo __init__() desta classe.
    version: int
    header_len: int  # Comprimento em bytes, e nao o valor bruto armazenado no pacote.
    tos: int         # Tambem chamado de bits DSCP e ECN.
    length: int      # Comprimento total do pacote.
    id: int
    flags: int
    frag_offset: int
    ttl: int
    proto: int
    cksum: int
    src: str
    dst: str

    def __init__(self, buffer: bytes):
        self.version = (buffer[0] >> 4) & 0x0F
        self.header_len = (buffer[0] & 0x0F) * 4
        self.tos = buffer[1]
        self.length = int.from_bytes(buffer[2:4], "big")
        self.id = int.from_bytes(buffer[4:6], "big")
        flags_offset = int.from_bytes(buffer[6:8], "big")
        self.flags = (flags_offset >> 13) & 0x07
        self.frag_offset = flags_offset & 0x1FFF
        self.ttl = buffer[8]
        self.proto = buffer[9]
        self.cksum = int.from_bytes(buffer[10:12], "big")
        self.src = f"{buffer[12]}.{buffer[13]}.{buffer[14]}.{buffer[15]}"
        self.dst = f"{buffer[16]}.{buffer[17]}.{buffer[18]}.{buffer[19]}"

    def __str__(self) -> str:
        return f"IPv{self.version} (tos 0x{self.tos:x}, ttl {self.ttl}, " + \
            f"id {self.id}, flags 0x{self.flags:x}, " + \
            f"offset {self.frag_offset}, " + \
            f"proto {self.proto}, header_len {self.header_len}, " + \
            f"len {self.length}, cksum 0x{self.cksum:x}) " + \
            f"{self.src} > {self.dst}"


class ICMP:
    # Cada membro abaixo corresponde a um campo do cabecalho ICMP. Os campos aparecem
    # na mesma ordem em que estao no pacote. Todos devem ser armazenados na ordem de
    # bytes do host.
    #
    # Modifique apenas o metodo __init__() desta classe.
    type: int
    code: int
    cksum: int

    def __init__(self, buffer: bytes):
        self.type = buffer[0]
        self.code = buffer[1]
        self.cksum = int.from_bytes(buffer[2:4], "big")

    def __str__(self) -> str:
        return f"ICMP (type {self.type}, code {self.code}, " + \
            f"cksum 0x{self.cksum:x})"


class UDP:
    # Cada membro abaixo corresponde a um campo do cabecalho UDP. Os campos aparecem
    # na mesma ordem em que estao no pacote. Todos devem ser armazenados na ordem de
    # bytes do host.
    #
    # Modifique apenas o metodo __init__() desta classe.
    src_port: int
    dst_port: int
    len: int
    cksum: int

    def __init__(self, buffer: bytes):
        self.src_port = int.from_bytes(buffer[0:2], "big")
        self.dst_port = int.from_bytes(buffer[2:4], "big")
        self.len = int.from_bytes(buffer[4:6], "big")
        self.cksum = int.from_bytes(buffer[6:8], "big")

    def __str__(self) -> str:
        return f"UDP (src_port {self.src_port}, dst_port {self.dst_port}, " + \
            f"len {self.len}, cksum 0x{self.cksum:x})"


def classificar_resposta_icmp(icmp: ICMP) -> str:
    if icmp.type == 11:
        return "tempo_excedido"
    elif icmp.type == 3:
        return "porta_inalcancavel"
    return "ignorar"


def calcular_inicio_cabecalho_transporte(buffer: bytes) -> int:
    return (buffer[0] & 0x0F) * 4


def deve_encerrar_traceroute(ip_origem: str, ip_destino: str, icmp: ICMP) -> bool:
    return ip_origem == ip_destino or classificar_resposta_icmp(icmp) == "porta_inalcancavel"


def registrar_roteador_descoberto(roteadores_ttl: list[str], endereco: str) -> None:
    if endereco not in roteadores_ttl:
        roteadores_ttl.append(endereco)


def interpretar_resposta_da_sonda(buffer: bytes) -> tuple[IPv4, ICMP | None]:
    ip = IPv4(buffer)
    deslocamento = calcular_inicio_cabecalho_transporte(buffer)
    icmp = None
    if ip.proto == util.IPPROTO_ICMP and len(buffer) >= deslocamento + 4:
        icmp = ICMP(buffer[deslocamento:])
    return ip, icmp


def traceroute(sendsock: util.Socket, recvsock: util.Socket, ip: str) \
        -> list[list[str]]:
    """Executa o traceroute e retorna o caminho descoberto.

    A funcao deve chamar util.print_result() com o resultado das sondas de cada TTL
    para mostrar o progresso da execucao.

    Argumentos:
    sendsock -- socket UDP usado para enviar as sondas do traceroute.
    recvsock -- socket no qual serao recebidas as respostas ICMP.
    ip -- endereco IP do host de destino.

    Retorno:
    Uma lista de listas representando os roteadores descobertos para cada TTL sondado.
    A lista de indice i contem todos os roteadores encontrados com uma sonda de TTL i+1.
    Os roteadores podem aparecer em qualquer ordem. Se nenhum roteador for encontrado,
    a lista correspondente pode ficar vazia. Se `ip` for descoberto, ele deve aparecer
    como o ultimo elemento da lista externa.
    """
    resultado: list[list[str]] = []

    for ttl in range(1, TRACEROUTE_MAX_TTL + 1):
        sendsock.set_ttl(ttl)
        roteadores_ttl: list[str] = []
        atingiu_destino = False

        for _ in range(PROBE_ATTEMPT_COUNT):
            sendsock.sendto(b"Potato", (ip, TRACEROUTE_PORT_NUMBER))
            if recvsock.recv_select():
                buf, _ = recvsock.recvfrom()
                ip_resp, icmp_resp = interpretar_resposta_da_sonda(buf)
                if icmp_resp is not None:
                    classificacao = classificar_resposta_icmp(icmp_resp)
                    if classificacao in ("tempo_excedido", "porta_inalcancavel"):
                        registrar_roteador_descoberto(roteadores_ttl, ip_resp.src)
                        if deve_encerrar_traceroute(ip_resp.src, ip, icmp_resp):
                            atingiu_destino = True

        util.print_result(roteadores_ttl, ttl)
        resultado.append(roteadores_ttl)

        if atingiu_destino:
            break

    return resultado


if __name__ == '__main__':
    args = util.parse_args()
    ip_addr = util.gethostbyname(args.host)
    print(f"traceroute to {args.host} ({ip_addr})")
    traceroute(util.Socket.make_udp(), util.Socket.make_icmp(), ip_addr)
