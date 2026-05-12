#!/usr/bin/env python3
"""Gera dados simulados de leads imobiliários seguindo o esquema do Jetimob."""

import csv
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

CORRETORES = [
    "Carlos Eduardo Silva",
    "Ana Paula Ferreira",
    "Roberto Mendes",
    "Juliana Costa",
    "Marcos Oliveira",
    "Fernanda Rodrigues",
    "Paulo Henrique Santos",
    "Camila Alves",
]

CLIENTES = [
    ("Gabriel Souza", "gabriel.souza"),
    ("Beatriz Lima", "beatriz.lima"),
    ("Diego Martins", "diego.martins"),
    ("Larissa Pereira", "larissa.pereira"),
    ("Rafael Torres", "rafael.torres"),
    ("Mariana Gomes", "mariana.gomes"),
    ("Thiago Carvalho", "thiago.carvalho"),
    ("Isabela Nascimento", "isabela.nasc"),
    ("Felipe Ribeiro", "felipe.ribeiro"),
    ("Amanda Castro", "amanda.castro"),
    ("Bruno Almeida", "bruno.almeida"),
    ("Natalia Rocha", "natalia.rocha"),
    ("Lucas Barbosa", "lucas.barbosa"),
    ("Patricia Dias", "patricia.dias"),
    ("Rodrigo Cunha", "rodrigo.cunha"),
    ("Camila Teixeira", "camila.teix"),
    ("Eduardo Moreira", "eduardo.mor"),
    ("Fernanda Lopes", "fernanda.lop"),
    ("Gustavo Nunes", "gustavo.nunes"),
    ("Helena Freitas", "helena.freitas"),
    ("Igor Pinto", "igor.pinto"),
    ("Julia Medeiros", "julia.med"),
    ("Leandro Santana", "leandro.sant"),
    ("Monica Correia", "monica.corr"),
    ("Nelson Xavier", "nelson.xavier"),
]

DOMINIOS_EMAIL = ["gmail.com", "hotmail.com", "outlook.com", "yahoo.com.br"]

CAMPANHAS = [
    "Google Ads - Apartamentos SP",
    "Meta - Novos Empreendimentos",
    "Indicação - Cliente",
    "Jetimob - Portal",
    "Instagram - Casarão SP",
    "Zap Imóveis",
    "OLX Imóveis",
    "LinkedIn Ads - Alto Padrão",
    "Site Orgânico",
    "Whatsapp - Indicação Direta",
]

MOTIVOS_PERDA = [
    "Preço acima do orçamento",
    "Não respondeu",
    "Comprou com outra imobiliária",
    "Desistiu da compra",
    "Sem perfil para financiamento",
    "Imóvel não atendeu expectativa",
    "Mudou de cidade",
    "Negociação travou",
]

PREFIXOS_IMOVEL = ["AP", "CS", "SL", "CO", "TE"]


def random_dt(start: datetime, end: datetime) -> datetime:
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))


def gerar_imovel() -> tuple[str, str, int]:
    """Retorna (codigo, categoria, valor_em_centavos)."""
    prefixo = random.choice(PREFIXOS_IMOVEL)
    codigo = f"{prefixo}-{random.randint(1000, 9999)}"
    categoria = random.choices(["novo", "usado"], weights=[40, 60])[0]
    # Faixas de valor realistas (em centavos) para SP
    if prefixo in ("AP", "SL"):
        valor = random.randint(25_000_000, 150_000_000)   # R$ 250k – R$ 1.5M
    elif prefixo == "CS":
        valor = random.randint(60_000_000, 250_000_000)   # R$ 600k – R$ 2.5M
    elif prefixo == "CO":
        valor = random.randint(40_000_000, 120_000_000)   # R$ 400k – R$ 1.2M
    else:  # TE
        valor = random.randint(80_000_000, 300_000_000)   # R$ 800k – R$ 3M
    return codigo, categoria, valor


def gerar_lead(lead_num: int, periodo_inicio: datetime, periodo_fim: datetime) -> dict:
    created_at = random_dt(periodo_inicio, periodo_fim)

    cliente_nome, cliente_base = random.choice(CLIENTES)
    dominio = random.choice(DOMINIOS_EMAIL)
    email = f"{cliente_base}{random.randint(1, 99)}@{dominio}"

    initial_owner = random.choice(CORRETORES)
    # 70% do tempo o corretor que fecha é o mesmo que captou
    final_owner = initial_owner if random.random() < 0.70 else random.choice(CORRETORES)

    contract_type = random.choices(["venda", "locação"], weights=[65, 35])[0]
    source_campaign = random.choice(CAMPANHAS)
    property_code, property_category, closed_value_cents = gerar_imovel()

    # SLA: primeira ação entre 0–48h após criação
    first_action_at = created_at + timedelta(hours=random.uniform(0.1, 48))
    # Primeiro contato: 0.5–6h após primeira ação
    first_contact_at = first_action_at + timedelta(hours=random.uniform(0.5, 6))

    # Resultado: 25% ganha, 50% perdida, 25% ainda em aberto
    outcome = random.choices(["won", "lost", "open"], weights=[25, 50, 25])[0]

    won_at = ""
    lost_at = ""
    loss_reason = ""
    closed_value = ""

    if outcome == "won":
        won_at = (first_contact_at + timedelta(days=random.randint(3, 90))).strftime(
            "%Y-%m-%dT%H:%M:%S"
        )
        # Locação tem ticket menor — usa centavos direto
        if contract_type == "locação":
            closed_value = round(random.randint(80_000, 500_000) / 100, 2)
        else:
            closed_value = round(closed_value_cents / 100, 2)
    elif outcome == "lost":
        lost_at = (first_contact_at + timedelta(days=random.randint(1, 60))).strftime(
            "%Y-%m-%dT%H:%M:%S"
        )
        loss_reason = random.choice(MOTIVOS_PERDA)

    return {
        "lead_id": str(uuid.uuid4()),
        "created_at": created_at.strftime("%Y-%m-%dT%H:%M:%S"),
        "client_name": cliente_nome,
        "client_email": email,
        "initial_owner": initial_owner,
        "final_owner": final_owner,
        "contract_type": contract_type,
        "source_campaign": source_campaign,
        "property_code": property_code,
        "first_action_at": first_action_at.strftime("%Y-%m-%dT%H:%M:%S"),
        "first_contact_at": first_contact_at.strftime("%Y-%m-%dT%H:%M:%S"),
        "won_at": won_at,
        "lost_at": lost_at,
        "loss_reason": loss_reason,
        "closed_value": closed_value,
        "property_category": property_category,
    }


def main():
    random.seed(42)  # reprodutível

    # Gerar leads distribuídos de 2025-Q1 até 2026-Q1
    periodos = [
        (datetime(2025, 1, 1), datetime(2025, 3, 31), 400),   # 2025-Q1
        (datetime(2025, 4, 1), datetime(2025, 6, 30), 500),   # 2025-Q2
        (datetime(2025, 7, 1), datetime(2025, 9, 30), 550),   # 2025-Q3
        (datetime(2025, 10, 1), datetime(2025, 12, 31), 450), # 2025-Q4
        (datetime(2026, 1, 1), datetime(2026, 3, 31), 150),   # 2026-Q1 (parcial)
    ]

    leads = []
    n = 0
    for inicio, fim, qtd in periodos:
        for _ in range(qtd):
            leads.append(gerar_lead(n, inicio, fim))
            n += 1

    # Ordenar por data de criação
    leads.sort(key=lambda x: x["created_at"])

    output = Path(__file__).parent.parent / "data" / "mock" / "leads.csv"
    fieldnames = list(leads[0].keys())

    with open(output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(leads)

    print(f"✓ {len(leads)} leads gerados em {output}")


if __name__ == "__main__":
    main()
