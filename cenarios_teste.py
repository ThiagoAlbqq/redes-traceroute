"""Cenarios determinísticos para testar manualmente a implementacao de traceroute.

Execute:
    python3 cenarios_teste.py

Os cenarios usam o simulador local; portanto, nao precisam de acesso a Internet nem de root.
"""

import traceroute as solucao
from simulador_rede import RedeSimulada


CENARIOS = [
    {
        "nome": "caminho_linear",
        "destino": "10.0.0.4",
        "saltos": [
            ["10.0.0.1"],
            ["10.0.0.2"],
            ["10.0.0.3"],
            ["10.0.0.4"],
        ],
        "esperado": [
            ["10.0.0.1"],
            ["10.0.0.2"],
            ["10.0.0.3"],
            ["10.0.0.4"],
        ],
    },
    {
        "nome": "multiplos_caminhos",
        "destino": "10.0.0.7",
        "saltos": [
            ["10.0.0.1"],
            ["10.0.0.2", "10.0.0.4"],
            ["10.0.0.3", "10.0.0.5"],
            ["10.0.0.6"],
            ["10.0.0.7"],
        ],
        "esperado": [
            ["10.0.0.1"],
            ["10.0.0.2", "10.0.0.4"],
            ["10.0.0.3", "10.0.0.5"],
            ["10.0.0.6"],
            ["10.0.0.7"],
        ],
    },
    {
        "nome": "salto_sem_resposta",
        "destino": "10.0.1.4",
        "saltos": [
            ["10.0.1.1"],
            [None],
            ["10.0.1.3"],
            ["10.0.1.4"],
        ],
        "esperado": [
            ["10.0.1.1"],
            [],
            ["10.0.1.3"],
            ["10.0.1.4"],
        ],
    },
]


def _print_result_local(routers, ttl):
    texto = ", ".join(routers) if routers else "*"
    print(f"{ttl: >2}: {texto}")


def normalizar(resultado):
    return [sorted(nivel) for nivel in resultado]


def executar_cenario(cenario):
    rede = RedeSimulada(cenario["destino"], cenario["saltos"])
    sendsock, recvsock = rede.sockets()

    # Evita consultas DNS reversas durante os testes locais.
    print_original = solucao.util.print_result
    solucao.util.print_result = _print_result_local
    try:
        obtido = solucao.traceroute(sendsock, recvsock, cenario["destino"])
    finally:
        solucao.util.print_result = print_original

    correto = normalizar(obtido) == normalizar(cenario["esperado"])
    print("Esperado:", cenario["esperado"])
    print("Obtido:  ", obtido)
    print("Resultado:", "OK" if correto else "DIVERGENTE")
    return correto


if __name__ == "__main__":
    acertos = 0
    for cenario in CENARIOS:
        print("\n===", cenario["nome"], "===")
        acertos += int(executar_cenario(cenario))
    print(f"\nCenarios corretos: {acertos}/{len(CENARIOS)}")
