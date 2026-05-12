# CLAUDE.md — Ecossistema de Dashboards e Automação Imobiliária

## Visão Geral do Projeto

Sistema de Business Intelligence e automação financeira para imobiliária, integrando o CRM Jetimob a dashboards analíticos segmentados por perfil de usuário. O objetivo central é eliminar processos manuais, fornecer visibilidade gerencial em tempo real e automatizar o motor de comissionamento da equipe comercial.

---

## Stack e Ferramentas

| Camada | Tecnologia |
|---|---|
| CRM | Jetimob (existente, não substituído) |
| Ingestão de Dados | Webhooks do Jetimob |
| Armazenamento | Google Sheets (fase inicial) / BigQuery (escala) |
| BI / Visualização | Looker Studio ou Web App Low-Code |
| Automação de Fluxos | n8n |
| Agente IA (futuro) | n8n + API oficial WhatsApp |

---

## Arquitetura de Dados

### Fonte Principal
Planilha centralizada (~2.000 registros) alimentada via webhook do Jetimob com os seguintes campos:

```
lead_id                  | string    — identificador único do lead
created_at               | datetime  — data de criação da oportunidade
client_name              | string
client_email             | string
initial_owner            | string    — corretor responsável na entrada
final_owner              | string    — corretor responsável no fechamento
contract_type            | enum      — venda | locação
source_campaign          | string    — fonte/campanha de origem
property_code            | string
first_action_at          | datetime  — primeira movimentação na esteira
first_contact_at         | datetime  — primeiro contato realizado
won_at                   | datetime  — data de fechamento (ganhou)
lost_at                  | datetime  — data de perda
loss_reason              | string
```

### Campos a Adicionar (Fase 1)
```
closed_value             | decimal   — valor efetivo fechado do imóvel
property_category        | enum      — novo | usado
```

---

## Dashboards

### Dashboard 1 — Comercial (Interno / Gestão)

**Audiência:** Gestores  
**Objetivo:** Raio-X do funil de vendas e SLA de atendimento

**Métricas:**
- Volume total de leads por período
- Tempo Médio de 1º Contato (SLA) por corretor
- Taxa de conversão por etapa do funil
- Vendas ganhas vs. perdidas

**Visualizações:**
- Funil de conversão de ponta a ponta
- Ranking gamificado de corretores (velocidade de atendimento + total de fechamentos)

**Restrições de Acesso:** Dados internos completos. Não compartilhar externamente.

---

### Dashboard 2 — Institucional (Construtoras / Parceiros)

**Audiência:** Construtoras parceiras  
**Objetivo:** Prestação de contas white-label de campanhas

**Métricas:**
- Volume de oportunidades por campanha/mídia
- Qualificação térmica dos leads: `Quente` / `Frio` / `Lixo`
- Evolução diária de geração de oportunidades

**Restrições de Acesso:**
- ❌ Sem dados de comissão ou repasse financeiro
- ❌ Sem desempenho individual da equipe
- ❌ Sem valores internos da imobiliária

---

### Dashboard 3 — Financeiro (Secretaria / Comissões)

**Audiência:** Equipe administrativa  
**Objetivo:** Cálculo automatizado e visualização de comissões

**Métricas:**
- VGV Acumulado no Trimestre
- Quantidade de vendas por corretor
- Status atual do corretor (Base / Prime)
- Valor exato a pagar em R$

**UX:**
- Tabela dinâmica e responsiva
- Código de cor semântico:
  - 🟢 **Verde** — corretor Prime (meta atingida)
  - ⚪ **Neutro** — corretor Base

---

## Motor de Comissionamento

### Regras Trimestrais

```
Taxa Base          → 35%  (todos os corretores no início do trimestre)

Gatilho Prime      → VGV ≥ R$ 2.100.000  OU  vendas ≥ 3
Taxa Prime         → 37%  (ao atingir o gatilho)

Acelerador         → +1% por venda adicional após atingir Prime
Teto Máximo        → 40%

Manutenção         → categoria travada pelo restante do trimestre vigente
```

### Lógica de Cálculo (pseudocódigo)

```python
def calcular_comissao(corretor, trimestre):
    vendas = get_vendas(corretor, trimestre)
    vgv    = sum(v.valor for v in vendas)
    
    # Define status
    if vgv >= 2_100_000 or len(vendas) >= 3:
        status = "Prime"
        taxa   = 0.37
        vendas_apos_prime = len(vendas) - 3  # vendas extras
        acelerador = min(vendas_apos_prime * 0.01, 0.03)  # máximo +3% → teto 40%
        taxa = min(taxa + acelerador, 0.40)
    else:
        status = "Base"
        taxa   = 0.35
    
    comissao = vgv * taxa
    return { "status": status, "taxa": taxa, "comissao": comissao }
```

> ⚠️ Regras sujeitas à consolidação final com lista oficial de corretores fornecida pelo cliente.

---

## Plano de Implementação

### Fase 1 — Fundação de Dados (Back-end)
- [ ] Validar regras de comissionamento e lista de corretores com cliente
- [ ] Adicionar campos `closed_value` e `property_category` no webhook do Jetimob
- [ ] Estruturar banco de dados no Google Sheets / BigQuery
- [ ] Criar Mock Data para desenvolvimento visual paralelo
- [ ] Implementar fórmulas de SLA (`first_contact_at - created_at`)

### Fase 2 — Construção dos Dashboards (Front-end / BI)
- [ ] Prototipar os 3 dashboards (Comercial, Institucional, Financeiro)
- [ ] Conectar base de dados ao Looker Studio ou Web App
- [ ] Homologar motor de comissão comparando com fechamentos históricos
- [ ] Configurar permissões de acesso por perfil de usuário

### Fase 3 — Agente IA WhatsApp (Expansão Futura)
- [ ] Criar agente no n8n integrado à API oficial do WhatsApp
- [ ] Alertas proativos: SLA de atendimento excedido → notificação ao corretor
- [ ] Consultas sob demanda via mensagem de texto:
  - Gestão: resumo diário do funil
  - Secretaria: `"Qual a comissão do corretor X neste trimestre?"`

---

## Convenções e Boas Práticas

- **Nomenclatura de campos:** `snake_case` em inglês
- **Datas:** ISO 8601 (`YYYY-MM-DDTHH:MM:SS`)
- **Valores monetários:** armazenados em centavos (inteiro) ou `DECIMAL(15,2)`, exibidos em BRL formatado
- **Trimestres:** sempre referenciar como `YYYY-Q{N}` (ex: `2025-Q2`)
- **Dados sensíveis:** comissões e repasses nunca devem trafegar para a camada institucional

---

## Integrações

```
Jetimob (CRM)
    └── Webhook (POST) ──→ Google Sheets / BigQuery
                               ├── Looker Studio (Dashboards)
                               └── n8n
                                    └── WhatsApp Business API (Fase 3)
```

---

## Contato e Contexto

- **Sistema CRM atual:** Jetimob
- **Volume inicial:** ~2.000 registros históricos
- **Tipo de negócio:** Imobiliária (venda + locação)
- **Perfis de usuário:** Gestor · Secretaria · Construtora Parceira
