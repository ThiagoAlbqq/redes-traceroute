"""Executa os 10 testes locais e calcula a nota percentual do projeto."""

import unittest
import testes


class ResultadoComNota(unittest.TextTestResult):
    """Resultado que conta cada metodo de teste apenas uma vez, inclusive com subtestes."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.testes_com_problema = set()

    def addFailure(self, test, err):
        self.testes_com_problema.add(test.id())
        super().addFailure(test, err)

    def addError(self, test, err):
        self.testes_com_problema.add(test.id())
        super().addError(test, err)

    def addSubTest(self, test, subtest, err):
        if err is not None:
            self.testes_com_problema.add(test.id())
        super().addSubTest(test, subtest, err)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(testes)
    runner = unittest.TextTestRunner(verbosity=2, resultclass=ResultadoComNota)
    resultado = runner.run(suite)

    total = resultado.testsRun
    reprovados = len(resultado.testes_com_problema)
    acertos = max(0, total - reprovados)
    percentual = 100.0 * acertos / total if total else 0.0
    nota_10 = percentual / 10.0

    print("\n=== RESULTADO DA AVALIACAO LOCAL ===")
    print(f"Testes aprovados: {acertos}/{total}")
    print(f"Percentual: {percentual:.0f}%")
    print(f"Nota correspondente (escala 0-10): {nota_10:.1f}")
    print("A nota deve ser validada na apresentacao ao professor.")
