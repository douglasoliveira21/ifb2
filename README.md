# Instituto Fiscaliza Brasil — IFB

Fiscalizamos resultados, não discursos.

Monorepo com **backend** (FastAPI + PostgreSQL) e **frontend** (Next.js) desacoplados,
prontos para deploy no EasyPanel como serviços Docker independentes.

Veja o desenho completo da arquitetura, banco de dados, páginas, design system,
indicadores e fontes em [`FASE-0.md`](./FASE-0.md).

## Estrutura

```
ifb/
├── backend/     # FastAPI + SQLAlchemy + Alembic
├── frontend/    # Next.js (App Router) + TypeScript + Tailwind
└── docker-compose.yml
```

## Rodando localmente com Docker

Requer Docker e Docker Compose.

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000 (docs em `/docs`)
- Postgres: localhost:5432 (usuário/senha/banco: `ifb`)

Para popular dados de **demonstração** (ambiente development apenas, nunca produção):

```bash
docker compose exec backend python -m app.sync.seed_dev
```

Para sincronizar os indicadores **reais** (desemprego, IPCA, Selic — fontes oficiais IBGE/BCB):

```bash
docker compose run --rm sync
```

## Rodando sem Docker

### Backend

Requer Python 3.12+.

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate  # Windows
pip install -e ".[dev]"
cp .env.example .env    # ajuste DATABASE_URL para seu Postgres local
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend

Requer Node 18+.

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Sem um backend rodando, a Home usa automaticamente dados de demonstração
(claramente identificados na tela) **somente quando `NODE_ENV=development`**.
Em produção, indicadores sem dado disponível exibem "Dado ainda não disponível" —
nunca um valor fictício.

## Deploy no EasyPanel

Cada serviço (`backend`, `frontend`, banco Postgres gerenciado pelo EasyPanel)
é publicado como um app Docker separado, usando os `Dockerfile` de cada pasta.
Configure as variáveis de ambiente de cada serviço conforme `.env.example`
(`DATABASE_URL` apontando para o Postgres do EasyPanel, `NEXT_PUBLIC_API_URL`
apontando para a URL pública do backend, `CORS_ORIGINS` com a URL do frontend).

A sincronização de dados (`app/sync/run.py`) não roda junto com o serviço web.
Configure no EasyPanel um segundo app a partir da mesma imagem do backend, do
tipo "Cron", com o comando `python -m app.sync.run` e um agendamento diário
(ex: `0 4 * * *`, fora do horário de pico). Isso evita manter um processo de
cron dentro do container da API e mantém os dois papéis (servir requisições x
sincronizar dados) desacoplados, sem precisar de Celery ou orquestrador externo.

### Indicadores integrados (Fases 2–4)

`app/sync/definitions.py` descreve os indicadores já integrados a fontes
oficiais via API pública, sem scraping:

| Indicador | Fonte | Série |
|---|---|---|
| Taxa de desemprego | IBGE (PNAD Contínua) | SGS/BCB 24369 |
| IPCA — 12 meses | IBGE | SGS/BCB 13522 |
| Selic (meta) | Banco Central | SGS/BCB 432 (consolidada por mês) |
| Dívida bruta do governo geral (% PIB) | Banco Central | SGS/BCB 13762 |
| Rendimento médio real habitual | IBGE (PNAD Contínua) | SGS/BCB 24382 |
| PIB mensal (valores correntes) | Banco Central | SGS/BCB 4380 |
| Resultado primário do governo central (12 meses) | Banco Central | SGS/BCB 5783 (sinal invertido — ver abaixo) |
| Desmatamento — Amazônia Legal | INPE (PRODES) | Arquivo de taxas anuais do TerraBrasilis (soma por período) |

Cada código de série do SGS/BCB usado aqui foi conferido manualmente contra o
histórico público conhecido antes de entrar no código — nunca um indicador é
adicionado com base em um código "chutado". Exemplos do que foi checado:
- Dívida/PIB: bate com o pico de ~87% na pandemia e a trajetória de queda depois.
- Rendimento médio real: reproduz o "efeito composição" documentado de 2020
  (renda média subiu porque a pandemia eliminou mais vagas de baixa renda,
  não porque os salários subiram) e a queda em 2021 com a alta da inflação.
- PIB mensal: mostra a queda de ~10% em abril/2020 (choque do lockdown).
- Resultado primário: o valor acumulado em 2020 bateu com o déficit conhecido
  de ~9,5% do PIB daquele ano — mas na convenção NFSP do BCB, onde positivo =
  déficit. `app/sync/bcb_client.py:invert_sign` inverte o sinal antes de
  gravar, para a convenção usual (positivo = superávit), documentada na
  metodologia do próprio indicador (`app/sync/definitions.py`).

- Desmatamento (PRODES/INPE): o desmatamento não vem do SGS/BCB — vem de um
  arquivo JSON estático (`rates2025.json`) que alimenta o próprio painel
  oficial do INPE (TerraBrasilis), descoberto inspecionando as chamadas de
  rede do painel no browser. O IFB soma as áreas de todos os estados da
  Amazônia Legal por período de 12 meses. Somando o período 08/2020–07/2021
  dá exatamente 13.038 km² — o valor exato do recorde de desmatamento
  amplamente noticiado naquele ciclo. Ver `app/sync/inpe_client.py`. O mesmo
  arquivo também traz a área por estado — o IFB grava essa série individual
  para os 9 estados da Amazônia Legal, usada nas páginas `/estados/[uf]`.

Nem todo candidato passou nessa checagem — um código testado para "resultado
primário" (buscando um valor já na convenção usual) e um para "rendimento
médio" (via SIDRA) tiveram os valores descartados por não baterem com o
histórico conhecido, e não foram usados.

PIB per capita não tem uma série simples equivalente no SGS/BCB (o Banco
Central não publica per capita — seria preciso combinar PIB com população,
outra fonte, e vira um indicador calculado, não um fetch direto). Fica para
uma iteração futura, junto com os indicadores que ainda dependem de fontes
sem API simples (DataSUS, INEP para IDEB/alfabetização, SNIS/SINISA):
mortalidade infantil, cobertura vacinal, expectativa de vida, IDEB,
alfabetização, homicídios e saneamento — cada uma exige um conector dedicado.

O sync é idempotente: rodar mais de uma vez não duplica dados, e qualquer
mudança em um valor já publicado (revisão da fonte) fica registrada em
`data_revisions` em vez de sobrescrever silenciosamente.

### Estados (Fase 5)

`/estados` lista os 27 estados (semeados por `app/sync/seed_states.py`, dado
factual estável — sigla e nome de UF, não estatística) com quantos
indicadores estão disponíveis, quantos melhoraram/pioraram e a última
atualização. `/estados/[uf]` mostra o placar de um estado específico.

Hoje só o desmatamento (PRODES) tem série por estado, e só para os 9 estados
da Amazônia Legal — os demais 18 estados, e os demais indicadores, mostram
"Dado ainda não disponível" em vez de qualquer valor inventado. Conforme
mais indicadores ganharem granularidade estadual (Fase 4 seguindo), essas
páginas passam a mostrar mais.

### Comparador (Fase 6)

`/comparar` tem dois modos, navegáveis por URL (`?modo=estados` ou
`?modo=periodos`), implementados como formulários GET em Server Components —
sem JavaScript client-side, links compartilháveis.

- **Estado × Estado**: compara os indicadores de dois estados lado a lado,
  indicador por indicador. Quando um estado não tem dado de um indicador,
  mostra "Dado ainda não disponível" em vez de omitir a linha silenciosamente.
- **Período × Período**: compara dois períodos de governo federal. Para cada
  indicador nacional, mostra o valor no início e no fim de cada período
  (`lib/period-compare.ts`). Sempre acompanhado do aviso de que correlação
  temporal não é causalidade.

Em nenhum dos dois modos o IFB calcula um "vencedor geral" — cada indicador é
mostrado separadamente, por design.

### Rankings (Fase 7)

`/rankings` lista rankings **calculados dinamicamente**: um indicador só vira
ranking se tiver dado em pelo menos 2 estados e polaridade não-neutra (a
Selic, por exemplo, nunca gera ranking — não faz sentido dizer que "subir"
é melhor ou pior). `/rankings/[slug]` mostra a tabela ordenada por variação
(mais melhora primeiro, considerando a direção do indicador).

Como só o desmatamento tem dado por estado hoje, só um ranking aparece
("Estados onde o desmatamento mais caiu", com os 9 estados da Amazônia
Legal). Não existe ranking geral de "melhor estado" — cada ranking é sobre
um único indicador, e a lista cresce sozinha conforme mais indicadores
ganham granularidade estadual.

### Admin e transparência (Fase 8)

`/admin` (protegido) e `/transparencia` (público) — a autenticação do admin
é **senha única via variável de ambiente** (`ADMIN_USERNAME`/`ADMIN_PASSWORD`,
mesma nos dois lados), decisão deliberada para não construir um sistema de
usuários completo num MVP de admin "extremamente pequeno". Sem
`ADMIN_PASSWORD` configurada, o admin fica **inacessível por padrão** — tanto
no middleware do Next.js (`proxy.ts`) quanto no backend (`app/core/security.py`).

- `/admin` — painel com contagem de indicadores/syncs/erros
- `/admin/indicadores` — habilitar/desabilitar indicador (sai das páginas
  públicas na hora; os dados continuam no banco)
- `/admin/sincronizacoes` — histórico de sync runs + botão para forçar uma
  sincronização agora (síncrono; se o número de fontes crescer muito, isso
  deve virar um job em background)
- `/admin/correcoes` — registra correção manual num valor específico.
  **Nunca sobrescreve em silêncio**: toda correção vira uma linha em
  `data_revisions`, com motivo obrigatório, antes e depois
- `/admin/metodologias` — versão vigente de cada indicador (edição continua
  sendo feita no código, `app/sync/definitions.py`)
- `/admin/fontes` — lista de fontes (somente leitura por enquanto)

`/transparencia` é pública e mostra fontes, últimas sincronizações, erros
conhecidos, correções recentes e metodologias — o próprio IFB precisa ser
auditável.

Para testar localmente: copie `.env.example` (raiz) para `.env` e defina
`ADMIN_PASSWORD`; o `docker-compose.yml` propaga a mesma senha para
`backend` e `frontend`.

## Testes

```bash
# backend (11 testes — sync, admin auth, headers de segurança)
cd backend && pytest

# frontend — lint + build
cd frontend && npm run lint && npm run build

# frontend — E2E (Playwright, mobile/tablet/desktop, roda com dados demo)
cd frontend && npx playwright install --with-deps chromium  # primeira vez
cd frontend && npm run test:e2e
```

A suíte E2E (`frontend/e2e/`) sobe o próprio `next dev` e testa contra os
dados de demonstração (não precisa do backend rodando). Cobre: Home,
Indicadores, Estados, Comparar (os dois modos), Rankings, 404, admin
inacessível sem senha, transparência pública, sitemap/robots, e uma checagem
de acessibilidade (axe-core, tags WCAG 2 A/AA) em 6 páginas — falha em
qualquer violação `serious` ou `critical`.

Essa suíte já pegou e corrigiu 3 bugs reais nesta fase: contraste insuficiente
do cinza `#737373` sobre `bg-gray-50` (ajustado para `#656565`), `<dt>`/`<dd>`
sem `<dl>` pai direto (estrutura semântica quebrada), e overflow horizontal
em 4 listagens no mobile (`min-w-0` faltando em texto longo dentro de flex).

## Performance, SEO e segurança (Fase 9)

- **SEO**: `app/sitemap.ts` (dinâmico, cobre indicadores/estados/rankings) e
  `app/robots.ts` (bloqueia `/admin`), Open Graph/Twitter card no layout raiz.
  `/metodologia` e `/fontes` foram criadas nesta fase — antes eram links
  quebrados no Header (404).
- **Acessibilidade**: skip link ("pular para o conteúdo"), foco visível
  consistente (`:focus-visible`, cor `--color-ink` em qualquer fundo),
  paleta de cinza ajustada para contraste AA, badges de classificação sempre
  com ícone + texto (nunca só cor).
- **Performance**: Server Components por padrão em toda a aplicação;
  `HistoryChart` é a única peça client-side pesada e já fica isolada por
  code-splitting automático por rota do Next.js (não entra no bundle de
  páginas que não usam gráfico); nenhuma biblioteca de gráficos foi usada
  (SVG próprio).
- **Segurança**: cabeçalhos `X-Content-Type-Options`, `X-Frame-Options`,
  `Referrer-Policy` e `Permissions-Policy` em toda resposta do backend
  (`app/core/security_headers.py`). HTTPS/TLS fica a cargo do proxy do
  EasyPanel na frente dos serviços.
