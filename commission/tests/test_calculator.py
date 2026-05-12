"""Testes do motor de comissionamento."""

from decimal import Decimal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from commission.calculator import (
    Venda,
    calcular_comissao,
    relatorio_trimestre,
    trimestre_de_data,
    VGV_GATILHO_PRIME,
    TAXA_BASE,
    TAXA_PRIME,
    TAXA_MAXIMA,
    TAXA_INTERMEDIACAO,
)


def _venda(corretor: str, valor: float, trimestre: str = "2025-Q2", contract_type: str = "venda") -> Venda:
    return Venda(
        lead_id="test",
        corretor=corretor,
        trimestre=trimestre,
        valor=Decimal(str(valor)),
        contract_type=contract_type,
    )


class TestStatusBase:
    def test_sem_vendas(self):
        r = calcular_comissao("Ana", "2025-Q2", [])
        assert r.status == "Base"
        assert r.taxa == TAXA_BASE
        assert r.vgv == Decimal("0")
        assert r.comissao == Decimal("0")

    def test_duas_vendas_abaixo_vgv(self):
        vendas = [_venda("Ana", 500_000), _venda("Ana", 400_000)]
        r = calcular_comissao("Ana", "2025-Q2", vendas)
        assert r.status == "Base"
        assert r.taxa == TAXA_BASE
        assert r.base_calculo == Decimal("900000") * TAXA_INTERMEDIACAO
        assert r.comissao == Decimal("900000") * TAXA_INTERMEDIACAO * TAXA_BASE

    def test_ignora_outros_corretores(self):
        vendas = [_venda("Carlos", 3_000_000)]  # Carlos tem VGV alto, não Ana
        r = calcular_comissao("Ana", "2025-Q2", vendas)
        assert r.status == "Base"


class TestGatilhoPrime:
    def test_prime_por_quantidade(self):
        """3 vendas de qualquer valor → Prime."""
        vendas = [_venda("Ana", 100_000) for _ in range(3)]
        r = calcular_comissao("Ana", "2025-Q2", vendas)
        assert r.status == "Prime"
        assert r.taxa == TAXA_PRIME

    def test_prime_por_vgv(self):
        """VGV ≥ R$ 2.100.000 com 2 vendas → Prime."""
        vendas = [_venda("Ana", 1_100_000), _venda("Ana", 1_200_000)]
        r = calcular_comissao("Ana", "2025-Q2", vendas)
        assert r.status == "Prime"

    def test_limite_exato_vgv(self):
        """VGV exatamente no limite → Prime."""
        vendas = [_venda("Ana", float(VGV_GATILHO_PRIME))]
        r = calcular_comissao("Ana", "2025-Q2", vendas)
        assert r.status == "Prime"

    def test_abaixo_limite_vgv(self):
        """Um centavo abaixo do limite com 2 vendas → Base."""
        vendas = [_venda("Ana", 2_099_999.99)]
        r = calcular_comissao("Ana", "2025-Q2", vendas)
        assert r.status == "Base"


class TestAcelerador:
    def test_4a_venda_38_pct(self):
        """4 vendas → taxa 38%."""
        vendas = [_venda("Ana", 200_000) for _ in range(4)]
        r = calcular_comissao("Ana", "2025-Q2", vendas)
        assert r.taxa == Decimal("0.38")

    def test_5a_venda_39_pct(self):
        vendas = [_venda("Ana", 200_000) for _ in range(5)]
        r = calcular_comissao("Ana", "2025-Q2", vendas)
        assert r.taxa == Decimal("0.39")

    def test_6a_venda_teto_40_pct(self):
        vendas = [_venda("Ana", 200_000) for _ in range(6)]
        r = calcular_comissao("Ana", "2025-Q2", vendas)
        assert r.taxa == TAXA_MAXIMA

    def test_muitas_vendas_nao_ultrapassa_teto(self):
        vendas = [_venda("Ana", 200_000) for _ in range(20)]
        r = calcular_comissao("Ana", "2025-Q2", vendas)
        assert r.taxa == TAXA_MAXIMA


class TestLocacao:
    def test_locacao_nao_conta_para_quantidade(self):
        """3 locações não ativam o Prime — não contam na quantidade."""
        vendas = [_venda("Ana", 100_000, contract_type="locação") for _ in range(3)]
        r = calcular_comissao("Ana", "2025-Q2", vendas)
        assert r.status == "Base"
        assert r.vgv == Decimal("0")
        assert r.num_vendas == 0

    def test_locacao_nao_conta_para_vgv(self):
        """Locações não entram no VGV mesmo com valor alto."""
        vendas = [_venda("Ana", 1_100_000, contract_type="locação") for _ in range(2)]
        r = calcular_comissao("Ana", "2025-Q2", vendas)
        assert r.status == "Base"
        assert r.vgv == Decimal("0")

    def test_misto_apenas_vendas_contam(self):
        """2 locações + 1 venda: VGV e contagem consideram só a venda."""
        vendas = [
            _venda("Ana", 500_000, contract_type="locação"),
            _venda("Ana", 500_000, contract_type="locação"),
            _venda("Ana", 300_000, contract_type="venda"),
        ]
        r = calcular_comissao("Ana", "2025-Q2", vendas)
        assert r.status == "Base"
        assert r.vgv == Decimal("300000")
        assert r.num_vendas == 1


class TestTrimestres:
    def test_trimestres_independentes(self):
        """Vendas de Q1 não influenciam Q2."""
        vendas = [_venda("Ana", 800_000, "2025-Q1") for _ in range(3)]
        r = calcular_comissao("Ana", "2025-Q2", vendas)
        assert r.status == "Base"
        assert r.vgv == Decimal("0")

    def test_trimestre_de_data(self):
        assert trimestre_de_data("2025-01-15T00:00:00") == "2025-Q1"
        assert trimestre_de_data("2025-04-01T00:00:00") == "2025-Q2"
        assert trimestre_de_data("2025-07-31T23:59:59") == "2025-Q3"
        assert trimestre_de_data("2025-10-01T00:00:00") == "2025-Q4"


class TestRelatorio:
    def test_relatorio_ordena_por_comissao(self):
        vendas = [
            _venda("Carlos", 500_000),
            _venda("Ana", 800_000),
            _venda("Ana", 900_000),
            _venda("Ana", 700_000),
        ]
        resultados = relatorio_trimestre("2025-Q2", vendas)
        assert resultados[0].corretor == "Ana"
        assert resultados[1].corretor == "Carlos"

    def test_relatorio_inclui_todos_corretores(self):
        vendas = [_venda("Ana", 300_000), _venda("Carlos", 300_000)]
        resultados = relatorio_trimestre("2025-Q2", vendas)
        nomes = {r.corretor for r in resultados}
        assert nomes == {"Ana", "Carlos"}


if __name__ == "__main__":
    import unittest

    # Roda todos os testes manualmente se pytest não estiver disponível
    total = passed = 0
    for cls_name, cls in list(globals().items()):
        if not cls_name.startswith("Test"):
            continue
        obj = cls()
        for method_name in dir(cls):
            if not method_name.startswith("test"):
                continue
            total += 1
            try:
                getattr(obj, method_name)()
                print(f"  ✓ {cls_name}.{method_name}")
                passed += 1
            except AssertionError as e:
                print(f"  ✗ {cls_name}.{method_name}: {e}")
            except Exception as e:
                print(f"  ✗ {cls_name}.{method_name}: {type(e).__name__}: {e}")
    print(f"\n{passed}/{total} testes passaram")
