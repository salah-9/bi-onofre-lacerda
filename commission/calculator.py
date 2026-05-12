"""Motor de comissionamento trimestral da imobiliária."""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional


@dataclass
class Venda:
    lead_id: str
    corretor: str
    trimestre: str          # formato YYYY-QN, ex: "2025-Q2"
    valor: Decimal          # valor fechado em R$ (não centavos)
    contract_type: str      # "venda" | "locação"


@dataclass
class ResultadoComissao:
    corretor: str
    trimestre: str
    status: str               # "Base" | "Prime"
    num_vendas: int
    vgv: Decimal              # soma dos valores dos imóveis (base do gatilho Prime)
    base_calculo: Decimal     # vgv × TAXA_INTERMEDIACAO (6%) — base real da comissão
    taxa: Decimal             # taxa do corretor: 35%–40%
    comissao: Decimal         # base_calculo × taxa

    def taxa_fmt(self) -> str:
        return f"{self.taxa * 100:.0f}%"

    def vgv_fmt(self) -> str:
        return f"R$ {self.vgv:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def comissao_fmt(self) -> str:
        return f"R$ {self.comissao:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# Constantes das regras de negócio
VGV_GATILHO_PRIME    = Decimal("2100000")
VENDAS_GATILHO_PRIME = 3
TAXA_BASE            = Decimal("0.35")
TAXA_PRIME           = Decimal("0.37")
ACELERADOR_POR_VENDA = Decimal("0.01")
TAXA_MAXIMA          = Decimal("0.40")
TAXA_INTERMEDIACAO   = Decimal("0.06")   # comissão da imobiliária sobre o valor do imóvel


def calcular_comissao(corretor: str, trimestre: str, vendas: list[Venda]) -> ResultadoComissao:
    """Calcula comissão de um corretor em um trimestre.

    Locações não contam para VGV nem para a contagem de vendas — apenas 'venda'.
    """
    vendas_trimestre = [
        v for v in vendas
        if v.corretor == corretor and v.trimestre == trimestre
    ]

    vendas_venda = [v for v in vendas_trimestre if v.contract_type == "venda"]
    vgv = sum((v.valor for v in vendas_venda), Decimal("0"))
    num_vendas = len(vendas_venda)

    atingiu_prime = vgv >= VGV_GATILHO_PRIME or num_vendas >= VENDAS_GATILHO_PRIME

    if atingiu_prime:
        status = "Prime"
        vendas_apos_prime = max(num_vendas - VENDAS_GATILHO_PRIME, 0)
        acelerador = min(vendas_apos_prime * ACELERADOR_POR_VENDA, TAXA_MAXIMA - TAXA_PRIME)
        taxa = min(TAXA_PRIME + acelerador, TAXA_MAXIMA)
    else:
        status = "Base"
        taxa = TAXA_BASE

    base_calculo = vgv * TAXA_INTERMEDIACAO
    comissao     = base_calculo * taxa

    return ResultadoComissao(
        corretor=corretor,
        trimestre=trimestre,
        status=status,
        num_vendas=num_vendas,
        vgv=vgv,
        base_calculo=base_calculo,
        taxa=taxa,
        comissao=comissao,
    )


def relatorio_trimestre(trimestre: str, vendas: list[Venda]) -> list[ResultadoComissao]:
    """Retorna o relatório de comissão de todos os corretores de um trimestre."""
    corretores = {v.corretor for v in vendas if v.trimestre == trimestre}
    resultados = [calcular_comissao(c, trimestre, vendas) for c in sorted(corretores)]
    return sorted(resultados, key=lambda r: r.comissao, reverse=True)


def trimestre_de_data(data_str: str) -> str:
    """Converte '2025-07-15T10:00:00' em '2025-Q3'."""
    mes = int(data_str[5:7])
    ano = data_str[:4]
    q = (mes - 1) // 3 + 1
    return f"{ano}-Q{q}"
