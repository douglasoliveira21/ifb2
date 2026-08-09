# FASE 0 — Instituto Fiscaliza Brasil (IFB)
### Arquitetura, banco, páginas, design system, indicadores, fontes e estratégia de recursos

> Documento de aprovação. Nenhum código será escrito até este documento ser validado.

---

## 1. Arquitetura geral

Monorepo com dois projetos independentes (frontend e backend desacoplados, comunicando via HTTP/REST), pensado para caber confortavelmente em **2 vCPU / 4 GB RAM** e para ser publicado no **EasyPanel** como serviços Docker separados.

```
ifb/
├── backend/                  # FastAPI (Python) — API + sincronização
│   ├── app/
│   │   ├── api/              # routers (indicators, locations, compare, rankings...)
│   │   ├── core/              # config, db session, security
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── services/           # cálculo de indicadores, comparação, ranking
│   │   ├── sync/               # conectores por fonte (ibge.py, bcb.py, inep.py...)
│   │   └── main.py
│   ├── alembic/                 # migrations
│   ├── tests/                    # pytest
│   ├── Dockerfile
│   └── pyproject.toml
│
├── frontend/                  # Next.js (TypeScript, App Router)
│   ├── app/                    # rotas (server components por padrão)
│   ├── components/
│   ├── lib/                     # cliente HTTP para a API, formatação de números
│   ├── styles/                   # design tokens, globals
│   ├── tests/                     # Playwright
│   ├── Dockerfile
│   └── package.json
│
├── docker-compose.yml           # ambiente local: db + backend + frontend
└── docs/
    └── FASE-0.md (este arquivo)
```

### Por que essa separação
- Frontend e backend escaláveis/deployáveis independentemente no EasyPanel (2 apps + 1 serviço de banco).
- Nenhuma dependência de runtime compartilhada entre os dois — o contrato é a API HTTP.
- Facilita cache de borda (ISR/HTTP cache) no frontend sem tocar no backend.

### Comunicação
- Frontend consome a API backend via HTTP em build/request time (Server Components fazem fetch direto do backend, sem expor a API a mais chamadas client-side do que o necessário).
- Contrato de API documentado via OpenAPI (gerado automaticamente pelo FastAPI) — serve também como documentação viva para o admin e futuros consumidores.

### Deploy (EasyPanel)
- 3 serviços Docker: `ifb-db` (Postgres, com volume persistente), `ifb-backend` (FastAPI, porta interna 8000), `ifb-frontend` (Next.js, porta interna 3000).
- Variáveis de ambiente via EasyPanel (DATABASE_URL, NEXT_PUBLIC_API_URL, etc.), nunca hardcoded.
- Sincronização roda como um **cron job dentro do próprio container backend** (ou serviço EasyPanel "Cron" separado rodando o mesmo Docker image com outro comando) — não precisa de orquestrador externo.
- Healthchecks simples (`/health` no backend) para o EasyPanel monitorar.

---

## 2. Estratégia para 2 vCPU / 4 GB RAM

- **Sem Redis, Celery, Kafka, Elasticsearch, pgvector, Kubernetes, microserviços** — confirmado, nada disso entra no MVP.
- Postgres com índices bem definidos assume o papel de cache de consulta; consultas de indicadores são agregações leves sobre tabelas pequenas (dezenas de indicadores × décadas de pontos mensais/anuais — no máximo dezenas de milhares de linhas no MVP).
- Cálculos pesados (variação, min/max, "o que mudou") são feitos **uma vez no sync**, gravados em tabelas/colunas derivadas — o frontend nunca recalcula em tempo real.
- Next.js usa **ISR (Incremental Static Regeneration)** para páginas de indicador/estado (revalidação a cada X horas, alinhada à frequência real de atualização dos dados) — a maior parte do tráfego é servida de cache estático, não bate no backend.
- Gráficos renderizados client-side apenas com os pontos necessários (JSON pequeno, sem datasets brutos no browser).
- Sync roda 1x/dia (ou conforme frequência da fonte) fora do horário de pico, curto (poucos indicadores no MVP), sem manter processos de longa duração.
- Estimativa de carga: backend FastAPI single worker (Uvicorn, 1-2 workers) atende tranquilamente o volume esperado de um instituto de dados no início.

---

## 3. Modelo de banco de dados (PostgreSQL)

Núcleo enxuto — 9 entidades, sem tabelas especulativas.

### `sources`
Fonte oficial de dados.
| campo | tipo | obs |
|---|---|---|
| id | uuid pk | |
| name | text | ex: "IBGE" |
| url | text | site institucional |
| description | text | |
| created_at | timestamptz | |

### `locations`
Brasil, estados (UF) — extensível para município no futuro, não usado no MVP.
| campo | tipo | obs |
|---|---|---|
| id | uuid pk | |
| type | enum(`country`,`state`) | |
| code | text | `BR`, `MG`, `SP`... |
| name | text | |

### `indicator_definitions`
Metadado fixo do indicador (não muda com o tempo).
| campo | tipo | obs |
|---|---|---|
| id | uuid pk | |
| slug | text unique | `desemprego` |
| name | text | "Taxa de desemprego" |
| category | enum | ECONOMIA, EMPREGO_RENDA, SAUDE, EDUCACAO, SEGURANCA, MEIO_AMBIENTE, INFRAESTRUTURA, CONTAS_PUBLICAS |
| unit | text | `%`, `R$`, `por 100 mil`... |
| polarity | enum(`higher_is_better`,`lower_is_better`,`neutral`) | define se subir é "melhora" |
| description_what | text | "O que este indicador mede?" |
| description_how | text | "Como interpretar?" |
| update_frequency | text | "mensal", "trimestral", "anual" |
| source_id | fk → sources | fonte primária |
| enabled | boolean | controla exibição (admin) |

### `indicator_methodologies`
Texto metodológico versionado por indicador (pode mudar ao longo do tempo, precisa de histórico).
| campo | tipo | obs |
|---|---|---|
| id | uuid pk | |
| indicator_id | fk | |
| version | int | |
| content | text (markdown) | |
| published_at | timestamptz | |

### `indicator_values`
Série histórica real — o coração do sistema.
| campo | tipo | obs |
|---|---|---|
| id | uuid pk | |
| indicator_id | fk | |
| location_id | fk | Brasil ou UF |
| reference_date | date | competência do dado (ex: 2026-07-01) |
| value | numeric | |
| collected_at | timestamptz | quando o IFB coletou |
| source_id | fk | |
| dataset_version | text nullable | versão/lote da fonte, se houver |
| is_revised | boolean default false | true se substitui valor anterior |
| created_at | timestamptz | |

Índice único lógico: (`indicator_id`, `location_id`, `reference_date`) para a versão vigente; revisões viram novas linhas referenciando a anterior via `data_revisions`.

### `government_periods`
Períodos de governo (federal e estadual) — usados apenas como referência histórica/eixo de comparação, nunca como "nota".
| campo | tipo | obs |
|---|---|---|
| id | uuid pk | |
| location_id | fk | Brasil ou UF |
| level | enum(`federal`,`state`) | |
| holder_name | text | nome do titular (informativo) |
| start_date | date | |
| end_date | date nullable | null = vigente |

### `sync_runs`
Log de cada execução de sincronização.
| campo | tipo | obs |
|---|---|---|
| id | uuid pk | |
| source_id | fk | |
| started_at | timestamptz | |
| finished_at | timestamptz nullable | |
| status | enum(`success`,`partial`,`error`) | |
| records_processed | int | |
| error_message | text nullable | |

### `data_revisions`
Registro de correções — manuais (admin) ou automáticas (série revisada pela fonte).
| campo | tipo | obs |
|---|---|---|
| id | uuid pk | |
| indicator_value_id | fk → indicator_values | valor corrigido |
| previous_value | numeric | |
| new_value | numeric | |
| reason | text | obrigatório |
| changed_by | text | `sync` ou usuário admin |
| changed_at | timestamptz | |

### `indicators` (view/materialized, não tabela editável)
Não é uma tabela de entrada manual — é uma **view materializada** (refeita a cada sync) que pré-calcula, por indicador × localização × período padrão: valor inicial, valor atual, variação, classificação (MELHOROU/PIOROU/ESTÁVEL/INCONCLUSIVO/SEM_DADOS). Isso é o que a Home e o Placar consultam — leitura O(1), sem cálculo em request-time.

**Total: 8 tabelas + 1 view materializada.** Nada além disso no MVP.

---

## 4. Mapa de páginas (MVP)

| Rota | Descrição |
|---|---|
| `/` | Home — Placar Brasil, Brasil em 60 segundos, O que mudou |
| `/indicadores` | Lista de indicadores por categoria |
| `/indicadores/[slug]` | Página individual do indicador (gráfico histórico, metodologia) |
| `/brasil/linha-do-tempo` | Linha do tempo interativa 2000→atual |
| `/estados` | Grid/lista dos 27 estados com placar resumido |
| `/estados/[uf]` | Página do estado |
| `/comparar` | Comparador (estado×estado, período×período) |
| `/rankings` | Lista de rankings disponíveis |
| `/rankings/[slug]` | Ranking objetivo específico |
| `/metodologia` | Metodologia geral |
| `/fontes` | Lista de fontes oficiais |
| `/transparencia` | Sincronizações, erros, correções, versões |
| `/admin` | Dashboard admin |
| `/admin/fontes`, `/admin/indicadores`, `/admin/sincronizacoes`, `/admin/metodologias`, `/admin/correcoes` | CRUD/monitoramento mínimo |

14 rotas públicas + 6 admin. Nenhuma página extra no MVP.

---

## 5. Design system (resumo executivo)

- **Cores**: `#F5C400` (amarelo IFB, institucional/destaque), `#111111` (preto, texto principal), `#FFFFFF`, `#F6F6F3`, `#ECECE7`, `#737373` (cinzas). Verde só para indicador positivo, vermelho só para negativo, cinza para neutro — sempre acompanhado de ícone + texto, nunca só cor (acessibilidade).
- **Tipografia**: Inter (ou Geist) para interface e dados; segunda fonte editorial opcional só em títulos institucionais grandes, avaliada durante Fase 1.
- **Padrão de layout**: editorial, não SaaS. Números grandes como elementos tipográficos primários, linhas divisórias finas, grid assimétrico, sem cards genéricos empilhados, sem sombra/gradiente/glass.
- **Componentes-base** (Fase 1): tipografia (escala de números grandes), linha divisória, tabela editorial, gráfico de linha minimalista (SVG próprio, sem biblioteca com estilo default visível), seletor de período, badge de classificação (MELHOROU/PIOROU/ESTÁVEL/INCONCLUSIVO/SEM DADOS).
- Detalhamento completo (tokens, espaçamento, grid, componentes) será entregue como parte da Fase 1, junto com o primeiro layout real.

---

## 6. Fontes oficiais (MVP)

| Fonte | Indicadores cobertos no MVP |
|---|---|
| IBGE | Desemprego (PNAD Contínua), IPCA, PIB, PIB per capita |
| Banco Central do Brasil (BCB/SGS) | Selic, Dívida/PIB, Resultado primário |
| Tesouro Nacional | Contas públicas complementares |
| INEP | IDEB, Alfabetização |
| DataSUS / Ministério da Saúde | Mortalidade infantil, cobertura vacinal, expectativa de vida |
| SENATRAN / Segurança pública (fonte a definir na Fase 2 — SUSP/Fórum Brasileiro de Segurança Pública) | Homicídios por 100 mil |
| SNIS/SINISA | Saneamento |
| INPE | Desmatamento |

Todas expõem API pública ou dados abertos em formato estruturado (CSV/JSON/SIDRA), compatíveis com um sync simples sem scraping pesado.

---

## 7. Lista inicial de indicadores (MVP — 16)

1. Taxa de desemprego (IBGE)
2. Rendimento médio real (IBGE)
3. IPCA (IBGE)
4. PIB (IBGE)
5. PIB per capita (IBGE)
6. Selic (BCB)
7. Dívida/PIB (BCB/Tesouro)
8. Resultado primário (Tesouro)
9. Mortalidade infantil (DataSUS)
10. Cobertura vacinal (DataSUS)
11. Expectativa de vida (IBGE/DataSUS)
12. IDEB (INEP)
13. Alfabetização (IBGE/INEP)
14. Homicídios por 100 mil (fonte a confirmar na Fase 2)
15. Saneamento — cobertura de água/esgoto (SNIS/SINISA)
16. Desmatamento (INPE, bioma Amazônia como referência inicial)

Todos com série histórica nacional; cobertura estadual será avaliada indicador a indicador na Fase 5 (nem todos têm série estadual confiável).

---

## 8. Estratégia de sincronização

```
scheduler (cron do container, ex: diário às 04:00)
  → script Python por fonte (backend/app/sync/<fonte>.py)
    → chamada à API oficial (SIDRA/IBGE, SGS/BCB, etc.)
      → normalização (unidade, competência, arredondamento)
        → upsert em indicator_values (nova linha se reference_date novo;
           se valor de reference_date existente mudou → registra em data_revisions)
          → grava sync_runs (status, registros processados, erro se houver)
            → REFRESH MATERIALIZED VIEW indicators (recalcula classificações)
```

- Um conector por fonte, isolado — falha em uma fonte não derruba as demais.
- Idempotente: rodar 2x no mesmo dia não duplica dados.
- Sem dado inventado: se a fonte não responde, o sync marca `error` em `sync_runs` e a página exibe a última data disponível — nunca um valor fictício.
- Correções manuais (admin) sempre passam por `data_revisions`, nunca sobrescrevem silenciosamente.

---

## 9. Aprovação necessária antes da Fase 1

Por favor confirme (ou peça ajustes em):
1. Estrutura de pastas e stack (Next.js + FastAPI + Postgres, Docker, EasyPanel).
2. Modelo de banco (8 tabelas + 1 view materializada).
3. Lista de 16 indicadores do MVP e fontes.
4. Mapa de 14 rotas públicas + 6 admin.
5. Direção de design system (resumo acima — detalhamento visual vem na Fase 1 com telas reais).

Com aprovação, a Fase 1 entrega: projeto Next.js + FastAPI + Postgres rodando localmente via `docker-compose`, schema criado via Alembic, Home e layout base com design system aplicado, e dados de demonstração explicitamente marcados como "development only".
