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
| Taxa de analfabetismo (15+ anos) | IBGE (PNAD Contínua) | SIDRA tabela 7113, variável 10267 |
| Esperança de vida ao nascer | IBGE (Projeção da População) | SIDRA tabela 7362, variável 2503 |
| Mortalidade infantil | IBGE (Projeção da População) | SIDRA tabela 7362, variável 1940 |
| PIB per capita (valores correntes) | IBGE (Contas Nacionais) | SIDRA tabela 6784, variável 9812 |
| IDEB — Anos Iniciais do Ens. Fundamental | INEP | Planilha de divulgação, aba "Brasil (Anos Iniciais)" |
| IDEB — Anos Finais do Ens. Fundamental | INEP | Planilha de divulgação, aba "Brasil (Anos Finais)" |
| IDEB — Ensino Médio | INEP | Planilha de divulgação, aba "Brasil (EM)" |
| Dívida consolidada líquida (% da RCL), por estado | Tesouro Nacional (SICONFI) | RGF, Anexo 02, fechamento do 3º quadrimestre |
| Despesa com pessoal (% da RCL), por estado | Tesouro Nacional (SICONFI) | RGF, Anexo 01, fechamento do 3º quadrimestre |
| Transferências constitucionais recebidas pelo estado | Tesouro Nacional | API de Transferências Constitucionais, somada por UF/ano |
| Taxa de escolarização (6 a 14 anos) | IBGE (PNAD Contínua) | SIDRA tabela 7138, variável 10276 |
| Taxa de escolarização (15 a 17 anos) | IBGE (PNAD Contínua) | SIDRA tabela 7138, variável 10276 |
| Receita total realizada, por estado | Tesouro Nacional (SICONFI) | RREO, Anexo 01, fechamento do 6º bimestre |

A Selic (série diária desde 1986) exige um cuidado extra: a API do BCB
recusa com 406 qualquer consulta a uma série diária cuja janela passe de
10 anos — inclusive o histórico completo sem filtro de data. Por isso
`app/sync/bcb_client.py:fetch_daily_series_chunked` busca em blocos de 10
anos e concatena o resultado antes de consolidar por mês. Esse limite não
existe em séries mensais (IPCA, dívida/PIB etc.), só nas diárias.

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

### API do SIDRA/IBGE (`app/sync/ibge_client.py`)

Diferente do SGS/BCB, cada tabela do SIDRA tem sua própria combinação de
variável + classificações (sexo, faixa etária...), então cada indicador
descreve sua consulta via `SidraQuery`. Os códigos foram descobertos
listando as tabelas de cada pesquisa do IBGE (`sidra.ibge.gov.br/pesquisa/
.../tabelas`) e confirmados com `desctabapi.aspx?c=<tabela>`, depois
validados contra números oficiais conhecidos antes de entrar no código —
mesmo padrão de rigor usado nas séries do BCB:
- Analfabetismo: 6,7% em 2016 caindo para 4,9% em 2025 — bate com a
  trajetória de queda amplamente divulgada pelo IBGE.
- Esperança de vida / mortalidade infantil: 69,83 anos / 29,02‰ em 2000,
  batendo com os números históricos oficiais.
- PIB per capita: R$ 51.693,92 em 2023, o valor exato divulgado pelo IBGE.

Duas armadilhas reais encontradas e corrigidas:
- A tabela de projeção populacional (7362) tem **dois** campos "Ano" na
  resposta — um fixo/irrelevante e outro que varia de verdade por linha.
  `_extract_year` pega o último, não o primeiro (ver comentário no código).
- Essa mesma tabela projeta até 2060. `drop_future_years` descarta
  qualquer ano ainda não decorrido antes de gravar — nunca um valor
  projetado é apresentado como se fosse observado.

### IDEB (`app/sync/inep_client.py`)

O INEP não expõe API para o IDEB — só planilha (.xlsx dentro de um .zip),
uma edição por vez. `app/sync/inep_client.py` baixa o zip da URL de
divulgação vigente, extrai a planilha e localiza o cabeçalho `VL_OBSERVADO_*`
dinamicamente (não hardcoda linha/coluna), lendo a linha "Total" (todas as
redes somadas) de cada aba: Anos Iniciais, Anos Finais e Ensino Médio —
gravados como três indicadores separados, para não inventar uma média
composta que a fonte não publica.

Os valores foram conferidos contra a série histórica amplamente conhecida do
IDEB Anos Iniciais Brasil: 3,8 (2005) → 6,3 (2025), incluindo a queda de 5,9
para 5,8 em 2021 por causa da pandemia. O IDEB só é apurado em anos ímpares
(a cada 2 anos, acompanhando o Censo Escolar e o SAEB) — não há dado para
anos pares, e essa lacuna é mostrada como é, não interpolada.

**Atenção ao manter**: a URL do zip (`IDEB_ZIP_URL` em
`app/sync/definitions.py`) é específica da edição 2025 — o INEP publica um
arquivo novo por edição, então essa URL precisa ser atualizada manualmente no
código quando sair a próxima edição (normalmente a cada 2 anos). Não há
quebra por estado nesta planilha (é a divulgação nacional consolidada).

**Certificado TLS incompleto**: `download.inep.gov.br` não envia o
certificado intermediário durante o handshake (confirmado com
`openssl s_client -showcerts`) — só clientes que buscam o intermediário
automaticamente (ex: Windows) conseguem validar a conexão; o OpenSSL usado
pelo Python em containers Linux falha com `CERTIFICATE_VERIFY_FAILED`. A
correção **não** é desativar a verificação do certificado: o intermediário
que falta (`RNP ICPEdu GR46 OV TLS CA 2025`, que termina numa raiz pública
da GlobalSign) está commitado em
`app/sync/certs/rnp_icpedu_gr46_ov_tls_ca_2025.pem` e é somado ao trust
store padrão (`certifi`) em `inep_client.py:_ssl_context`.

Indicadores que ainda dependem de fontes sem API simples (exigem simulação de
formulário/dashboard, não um fetch direto): cobertura vacinal (DataSUS/PNI),
homicídios (sem fonte honesta encontrada — Registro Civil do IBGE mistura
óbitos não naturais de várias causas) e saneamento (SNIS/SINISA, dashboard em
Power BI) — cada uma exigiria um conector dedicado bem mais complexo, fora do
escopo desta iteração.

**Setor Saúde investigado e descartado por ora**: antes de integrar dados de
saúde, testamos ao vivo as três fontes mais promissoras e nenhuma passou no
mesmo padrão de confiabilidade aplicado às demais integrações. Leitos SUS
(API DEMAS/CNES, `apidadosabertos.saude.gov.br/assistencia-a-saude/hospitais-e-leitos`)
tem o filtro `uf` retornando erro 500 de forma consistente, e a paginação por
`offset` não termina de forma sensata (testado até offset=5000 × limit=1000,
sempre devolvendo página cheia — implicaria milhões de hospitais, o que não
existe). O Portal de Dados Abertos do SUS (`dadosabertos.saude.gov.br`)
retornou erro 500 no site inteiro durante o teste. SIOPS (gasto em saúde por
estado) não tem API JSON, só um sistema de consulta em formulário PHP antigo
(`siops.datasus.gov.br`). A tabela SIDRA 216 (leitos por habitante, Pesquisa
de Assistência Médico-Sanitária/IBGE) existe e é estável, mas os dados param
em 2005 — a pesquisa foi descontinuada, não serve para avaliar gestão atual.
Antes de retomar este setor, vale testar novamente se o DEMAS/CNES
estabilizou, ou buscar um dataset CSV estático (como o padrão já usado para
o IDEB) em vez de depender da API ao vivo.

### Contas públicas por estado (`app/sync/siconfi_client.py`, `app/sync/tesouro_transferencias_client.py`)

Dívida consolidada líquida, despesa com pessoal (ambas como % da Receita
Corrente Líquida — RCL — ajustada) e receita total realizada vêm do
**SICONFI** (Tesouro Nacional) — API pública sem autenticação, mas sem
documentação completa dos parâmetros de consulta publicada pelo Tesouro. Os
parâmetros usados
(`id_ente`, `in_periodicidade`, `co_tipo_demonstrativo`, `no_anexo`,
`co_poder`) e os nomes de conta/coluna (`cod_conta`, `coluna`) foram
descobertos e confirmados empiricamente contra a API real: para São Paulo
(id_ente=35) em 2023, a % da DCL sobre a RCL ajustada retornada foi 127,92%
e a % de despesa com pessoal foi 42,33% — ambos consistentes com números de
dívida estadual de SP amplamente noticiados (o estado carrega uma das
maiores relações dívida/RCL do país, herdada da renegociação de dívida com
a União nos anos 1990). O RGF é declarado por estado a cada quadrimestre; o
IFB sincroniza sempre o fechamento do 3º quadrimestre (ano completo) como o
valor anual. Não há dado no SICONFI para exercícios anteriores a 2015
(testado e confirmado: consultas para 2010–2014 sempre retornam 0
registros).

A API do SICONFI tem um bug de codificação de caracteres conhecido — o
texto de `coluna` chega com acentos/símbolos corrompidos mesmo com
`Content-Type: application/json; charset=utf-8` declarado. `siconfi_client.py`
contorna isso comparando só os trechos ASCII estáveis da coluna (ex: `"o 3"`
+ `"Quadrimestre"` no RGF, `"(c)"` + `"Bimestre"` no RREO) em vez do texto
completo.

A receita total realizada usa o **RREO** (Relatório Resumido da Execução
Orçamentária) em vez do RGF — mesmo host e mesmo padrão de retry, mas
endpoint (`/rreo`), períodos (6 bimestres, não 3 quadrimestres) e nomes de
conta diferentes. Testado contra São Paulo em 2023: R$ 326,7 bilhões de
receita total realizada, na mesma ordem de grandeza do orçamento estadual
de SP amplamente divulgado na imprensa. Diferente do RGF, o RREO não é
filtrado por `co_poder` — o valor já vem consolidado para o governo
estadual inteiro.

**Transferências constitucionais recebidas pelo estado** vem da **API de
Transferências Constitucionais do Tesouro Nacional** — FPE, FUNDEB,
royalties (petróleo, Itaipu, recursos hídricos/minerais), IPI-Exportação,
Lei Kandir, CIDE-Combustíveis, IOF-Ouro e demais repasses obrigatórios
previstos em lei (não inclui convênios nem emendas parlamentares). API
pública **sem autenticação**, confirmada ao vivo: uma única requisição com
`p_estado` e `p_ano` listando todos os 27 estados e todos os anos (valores
separados por `:`) retorna ~23 mil linhas (estado × ano × mês × tipo de
transferência), que o IFB soma por estado e ano.

Esta API não tem documentação pública indexada por buscador nem um
`swagger.json` acessível diretamente por URL — a única forma de descobrir a
URL real (`https://apiapex.tesouro.gov.br/aria/`) e os parâmetros de
consulta foi carregar a página de visualização do Tesouro
(`sisweb.tesouro.gov.br/apex/f?p=10250:7:...`) em um browser e capturar a
chamada de rede que busca a especificação OpenAPI embutida na própria
página. Essa especificação avisa "para solicitar acesso, entrar em contato
com desenvolvimento@tesouro.gov.br", mas na prática a API responde sem
qualquer chave — o aviso provavelmente se refere a um nível de acesso mais
amplo (dados por município) do que o usado aqui.

Antes de escolher esta fonte, também testamos o Portal da Transparência
(CGU) para o mesmo indicador, mas descartamos: exige cadastro de chave de
API, e não havia como validar a resposta real nesta sessão. A API do
Tesouro cobre exatamente o mesmo conceito (transferências obrigatórias por
estado) sem essa fricção, então foi a escolha final.

### Indicadores por estado

Cinco dos indicadores do SIDRA (analfabetismo, esperança de vida, mortalidade
infantil, e as duas taxas de escolarização) também são sincronizados **por
UF** — o SIDRA aceita nível territorial `n3` retornando as 27 UFs de uma vez
(`fetch_sidra_series_by_state` em `app/sync/ibge_client.py`). PIB per capita
(tabela 6784) não tem quebra por estado no SIDRA, só nível Brasil.

As taxas de escolarização (tabela 7138, variável 10276) mostram a
universalização quase completa do Ensino Fundamental (6 a 14 anos: acima de
97% em praticamente todos os estados) contra uma queda visível na idade do
Ensino Médio (15 a 17 anos: entre ~89% e ~95% conforme o estado, 2025) — os
dois indicadores juntos evidenciam onde a evasão escolar se concentra,
estado a estado.

Isso soma ao desmatamento (9 estados da Amazônia Legal, via INPE) e aos três
indicadores de contas públicas por estado (dívida consolidada líquida,
despesa com pessoal — ambos via SICONFI — e transferências constitucionais,
via API do Tesouro Nacional, todos para os 27 estados) para dar conteúdo de
verdade a `/estados/[uf]` e ao comparador Estado × Estado.

A busca por estado é isolada da mesma forma que os indicadores nacionais:
se a chamada à API falhar antes de processar qualquer UF, vira um registro
de erro em `sync_runs` em vez de derrubar o resto da sincronização
(`app/sync/run.py:sync_by_state`).

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
