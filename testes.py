"""Testes locais do Projeto 1 - Traceroute.

Ha exatamente 10 testes. Cada teste vale 10% da avaliacao automatizada local.
A nota obtida deve ser validada na apresentacao ao professor.
"""

import unittest
from unittest.mock import patch

import traceroute as solucao
from simulador_rede import RedeSimulada, construir_ipv4, construir_icmp, construir_udp


class TestesProjeto1(unittest.TestCase):
    def test_01_ipv4_basico(self):
        payload = b"abc"
        pacote = construir_ipv4(
            "1.2.3.4", "5.6.7.8", 17, payload,
            ttl=37, identificacao=0xBEEF, flags=2, offset=123, tos=0x20,
        )
        ip = solucao.IPv4(pacote[:20])
        self.assertEqual(ip.version, 4)
        self.assertEqual(ip.header_len, 20)
        self.assertEqual(ip.tos, 0x20)
        self.assertEqual(ip.length, 23)
        self.assertEqual(ip.id, 0xBEEF)
        self.assertEqual(ip.flags, 2)
        self.assertEqual(ip.frag_offset, 123)
        self.assertEqual(ip.ttl, 37)
        self.assertEqual(ip.proto, 17)
        self.assertEqual(ip.src, "1.2.3.4")
        self.assertEqual(ip.dst, "5.6.7.8")

    def test_02_ipv4_com_opcoes(self):
        pacote = construir_ipv4(
            "203.0.113.1", "198.51.100.9", 1, b"x",
            ttl=9, ihl=6, opcoes=b"\x01\x02\x03\x04", identificacao=321,
        )
        ip = solucao.IPv4(pacote[:24])
        self.assertEqual(ip.version, 4)
        self.assertEqual(ip.header_len, 24)
        self.assertEqual(ip.length, 25)
        self.assertEqual(ip.id, 321)
        self.assertEqual(ip.proto, 1)
        self.assertEqual(ip.src, "203.0.113.1")
        self.assertEqual(ip.dst, "198.51.100.9")

    def test_03_ipv4_campos_variados(self):
        casos = [
            ("10.1.2.3", "10.9.8.7", 1, 1, 0, 0, 0),
            ("172.16.0.1", "8.8.8.8", 17, 255, 7, 8191, 255),
            ("192.0.2.55", "203.0.113.99", 17, 64, 1, 2048, 7),
        ]
        for src, dst, proto, ttl, flags, offset, tos in casos:
            with self.subTest(src=src, dst=dst):
                pacote = construir_ipv4(
                    src, dst, proto, b"dados", ttl=ttl,
                    flags=flags, offset=offset, tos=tos,
                )
                ip = solucao.IPv4(pacote[:20])
                self.assertEqual((ip.src, ip.dst), (src, dst))
                self.assertEqual(ip.proto, proto)
                self.assertEqual(ip.ttl, ttl)
                self.assertEqual(ip.flags, flags)
                self.assertEqual(ip.frag_offset, offset)
                self.assertEqual(ip.tos, tos)

    def test_04_icmp(self):
        cab = construir_icmp(11, 0)[:8]
        icmp = solucao.ICMP(cab)
        self.assertEqual(icmp.type, 11)
        self.assertEqual(icmp.code, 0)
        self.assertEqual(icmp.cksum, 0)

    def test_05_udp(self):
        cab = construir_udp(12345, 33434, b"abcd")[:8]
        udp = solucao.UDP(cab)
        self.assertEqual(udp.src_port, 12345)
        self.assertEqual(udp.dst_port, 33434)
        self.assertEqual(udp.len, 12)
        self.assertEqual(udp.cksum, 0)

    def _executar(self, destino, saltos):
        rede = RedeSimulada(destino, saltos)
        sendsock, recvsock = rede.sockets()
        with patch.object(solucao.util, "print_result") as imprimir:
            resultado = solucao.traceroute(sendsock, recvsock, destino)
        return resultado, imprimir

    @staticmethod
    def _normalizar(resultado):
        return [sorted(nivel) for nivel in resultado]

    def test_06_traceroute_linear(self):
        esperado = [["10.0.0.1"], ["10.0.0.2"], ["10.0.0.3"], ["10.0.0.4"]]
        obtido, _ = self._executar("10.0.0.4", esperado)
        self.assertEqual(self._normalizar(obtido), self._normalizar(esperado))

    def test_07_traceroute_multiplos_caminhos(self):
        saltos = [
            ["10.0.0.1"],
            ["10.0.0.2", "10.0.0.4"],
            ["10.0.0.3", "10.0.0.5"],
            ["10.0.0.6"],
            ["10.0.0.7"],
        ]
        obtido, _ = self._executar("10.0.0.7", saltos)
        self.assertEqual(self._normalizar(obtido), self._normalizar(saltos))

    def test_08_traceroute_salto_sem_resposta(self):
        saltos = [["10.0.1.1"], [None], ["10.0.1.3"], ["10.0.1.4"]]
        esperado = [["10.0.1.1"], [], ["10.0.1.3"], ["10.0.1.4"]]
        obtido, _ = self._executar("10.0.1.4", saltos)
        self.assertEqual(self._normalizar(obtido), self._normalizar(esperado))

    def test_09_traceroute_remove_duplicatas(self):
        saltos = [
            ["10.0.2.1", "10.0.2.1", "10.0.2.1"],
            ["10.0.2.2", "10.0.2.2", "10.0.2.2"],
            ["10.0.2.3"],
        ]
        esperado = [["10.0.2.1"], ["10.0.2.2"], ["10.0.2.3"]]
        obtido, _ = self._executar("10.0.2.3", saltos)
        self.assertEqual(self._normalizar(obtido), self._normalizar(esperado))

    def test_10_para_ao_encontrar_destino_e_imprime_por_ttl(self):
        saltos = [
            ["10.0.3.1"],
            ["10.0.3.2"],
            ["10.0.3.3"],
            ["10.0.3.4"],  # Estes niveis nao devem ser sondados.
        ]
        obtido, imprimir = self._executar("10.0.3.3", saltos)
        esperado = [["10.0.3.1"], ["10.0.3.2"], ["10.0.3.3"]]
        self.assertEqual(self._normalizar(obtido), self._normalizar(esperado))
        self.assertEqual(imprimir.call_count, 3)
        self.assertEqual(imprimir.call_args_list[-1].args, (["10.0.3.3"], 3))


if __name__ == "__main__":
    unittest.main(verbosity=2)
