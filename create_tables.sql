-- BI Onofre Lacerda — criação de tabelas no Supabase
-- Rodar no SQL Editor do Supabase (app.supabase.com → projeto → SQL Editor)

-- ─────────────────────────────────────────────────────────────────
-- 1. LEADS CONSOLIDADOS
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS leads_consolidados (
    id               BIGSERIAL PRIMARY KEY,
    lead_id          TEXT,
    created_at       TIMESTAMP,
    client_name      TEXT,
    client_email     TEXT,
    initial_owner    TEXT,
    final_owner      TEXT,
    contract_type    TEXT,
    source           TEXT,
    first_action_at  TIMESTAMP,
    first_contact_at TIMESTAMP,
    won_at           TIMESTAMP,
    lost_at          TIMESTAMP,
    loss_reason      TEXT,
    regiao           TEXT
);

-- ─────────────────────────────────────────────────────────────────
-- 2. OP GANHAS
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS op_ganhas (
    id                 BIGSERIAL PRIMARY KEY,
    lead_id            TEXT,
    won_at             TIMESTAMP,
    corretor           TEXT,   -- "Responsavel" na planilha
    captador           TEXT,
    trimestre          TEXT,   -- ex: "2025-Q1"
    mes                TEXT,   -- ex: "2025-03"
    tipo_negocio       TEXT,   -- "Venda" | "Locação"
    tipo_imovel        TEXT,   -- "Novo" | "Usado"
    regiao             TEXT,
    valor              NUMERIC(15,2),
    comissao_total     NUMERIC(15,2),
    r_corretor         NUMERIC(15,2),
    r_captador         NUMERIC(15,2),
    r_gestao           NUMERIC(15,2),
    vgv_acumulado      NUMERIC(15,2),
    categoria_venda    TEXT,   -- "prime" | "prime+1" | "prime+2" | "prime+3"
    prime_herdado_flag TEXT    -- "SIM" | ""
);

-- ─────────────────────────────────────────────────────────────────
-- 3. PRIME HERDADO
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS prime_herdado (
    id             BIGSERIAL PRIMARY KEY,
    corretor_prime TEXT,
    trimestre      TEXT
);

-- ─────────────────────────────────────────────────────────────────
-- Índices úteis para performance
-- ─────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_leads_created_at  ON leads_consolidados (created_at);
CREATE INDEX IF NOT EXISTS idx_leads_won_at      ON leads_consolidados (won_at);
CREATE INDEX IF NOT EXISTS idx_ganhas_trimestre  ON op_ganhas (trimestre);
CREATE INDEX IF NOT EXISTS idx_ganhas_mes        ON op_ganhas (mes);
CREATE INDEX IF NOT EXISTS idx_ganhas_corretor   ON op_ganhas (corretor);
