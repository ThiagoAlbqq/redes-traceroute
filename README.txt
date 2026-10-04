PROJETO 1 - TRACEROUTE

Arquivos para o aluno
---------------------
traceroute.py       Arquivo que deve ser implementado.
util.py             Funcoes auxiliares. Nao modificar.
simulador_rede.py   Simulador local deterministico, sem root e sem rede real.
cenarios_teste.py   Cenarios de depuracao executaveis.
testes.py           Conjunto de 10 testes locais.
avaliar.py          Executa os testes e calcula percentual/nota.

Como testar
-----------
1. Implemente traceroute.py.
2. Execute os cenarios de depuracao:
       python3 cenarios_teste.py
3. Execute a avaliacao local:
       python3 avaliar.py

A avaliacao possui 10 testes. Cada teste aprovado corresponde a 10%.
O percentual de testes aprovados corresponde a nota tecnica do projeto; em escala 0-10,
100% = 10,0, 90% = 9,0, etc. Essa nota deve ser validada em apresentacao ao professor.

Execucao em rede real (opcional para depuracao)
-----------------------------------------------
No Linux, pode ser necessario usar privilegios administrativos para receber ICMP:
       sudo python3 traceroute.py cmu.edu

Os testes oficiais fornecidos com o projeto usam o simulador local e nao dependem de
roteadores reais, de acesso a Internet ou de privilegios de administrador.
