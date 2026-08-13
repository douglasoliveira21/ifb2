# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Usuário primário (confirmado): o cidadão comum brasileiro — sem formação técnica em economia, estatística ou políticas públicas — que quer entender, em minutos, se indicadores concretos do país (emprego, inflação, saúde, educação, meio ambiente, contas públicas) estão melhorando ou piorando, sem depender de discurso político para saber isso.

Usuários secundários (inferido do escopo do produto — páginas `/admin`, `/transparencia`, comparador, rankings): jornalistas e pesquisadores que citam o IFB como fonte, e cidadãos que usam o comparador Estado×Estado ou Período×Período para cobrar governantes com dado, não opinião. O design deve continuar legível para leigos mesmo quando serve esse público mais técnico — nunca o contrário.

## Product Purpose

O Instituto Fiscaliza Brasil (IFB) fiscaliza **resultados** de políticas públicas brasileiras, não discursos — reunindo indicadores oficiais (BCB, IBGE, INPE, INEP e outras fontes governamentais) num só lugar, com histórico, metodologia e fonte visíveis para cada número.

Sucesso = o visitante sai sabendo, para um indicador específico, "o que é", "como mudou ao longo do tempo" e "de onde vem esse número" — sem o IFB ter dito a ele o que pensar sobre isso.

## Positioning

"Fiscalizamos resultados, não discursos": o IFB nunca atribui automaticamente um resultado a um governante ou período — mostra correlação temporal com um aviso explícito de que correlação não é causalidade, deixando a interpretação política para o visitante. Nenhum concorrente de "dashboard de indicadores" se compromete estruturalmente com essa neutralidade: todo valor exibido carrega `source_id`, `source_url` e uma metodologia versionada, e a ausência de dado aparece como "Dado ainda não disponível" — nunca um placeholder ou valor inventado.

## Operating Context

- Sincronização automatizada roda uma vez por dia (cron/job separado no container backend), buscando direto das APIs/planilhas oficiais — nunca scraping de conteúdo interpretado por terceiros.
- Cada fonte sincroniza isolada: a falha de uma (timeout, certificado, mudança de formato) nunca derruba as demais; erros ficam registrados em `sync_runs` e visíveis em `/transparencia`.
- Correções manuais de valor passam por `/admin/correcoes` e sempre geram uma linha auditável em `data_revisions` — nunca sobrescrevem em silêncio.
- Rodando em infraestrutura enxuta (2 vCPU / 4 GB, EasyPanel) — sem Redis, Celery ou microserviços; o design e as decisões técnicas devem continuar cabendo nesse orçamento.

## Capabilities and Constraints

- Stack existente: backend FastAPI + PostgreSQL (com materialized view para os resumos de indicador), frontend Next.js (App Router, Server Components por padrão) + TypeScript + Tailwind CSS v4.
- Indicadores cobrem: economia, contas públicas, emprego/renda, educação (incluindo IDEB), saúde, meio ambiente, segurança, demografia — em nível Brasil e, quando a fonte permite, por estado/município.
- Nunca fabricar ou estimar um dado que a fonte não publicou. Um indicador sem dado mostra "Dado ainda não disponível", nunca um número interpolado ou um zero.
- Classificação "melhorou"/"piorou" só aparece quando metodologicamente justificável (indicador tem polaridade clara — ex: Selic não tem "lado bom", então nunca é classificada).
- `/admin` protegido por HTTP Basic Auth de senha única (variável de ambiente); sem senha configurada, fica inacessível por padrão — não há sistema de usuários completo.

## Brand Commitments

- Nome fixo: **Instituto Fiscaliza Brasil (IFB)**.
- Identidade visual editorial/institucional, deliberadamente **não** parecida com um dashboard de SaaS — o IFB é fiscalização pública, não uma ferramenta de analytics.
- Paleta base: amarelo de destaque `#F5C400`, tinta `#111111`, escala de cinzas neutros (ver `frontend/app/globals.css` / tokens existentes) — preservar, não redesenhar, salvo pedido explícito de rebrand.
- Tom de voz institucional e factual: frases como "Fiscalizamos resultados, não discursos" são compromissos de marca, não apenas copy de marketing — todo texto de UI deve honrar essa neutralidade.

## Evidence on Hand

- Indicadores reais já sincronizados e ao vivo em produção (não são dados de demonstração): desemprego, IPCA, Selic, dívida/PIB, rendimento médio real, PIB mensal, resultado primário, desmatamento (PRODES/INPE, com série por estado), analfabetismo, esperança de vida, mortalidade infantil, PIB per capita, IDEB (3 etapas), e um conjunto maior ainda sendo expandido (feminicídio, carga tributária, mortalidade materna, entre outros — ver `backend/app/sync/definitions.py`).
- Metodologia de cada indicador documentada em Markdown, versionada em `indicator_methodologies`, e exposta tanto na página do indicador quanto em `/transparencia`.
- Nenhum depoimento, estudo de caso, ou prova social deve ser inventado — o IFB não tem (nem precisa de) testemunhos de clientes; a prova de credibilidade é a fonte oficial de cada número.

## Product Principles

1. **Resultado, não discurso** — nunca atribuir automaticamente um número a um governante; correlação temporal sempre vem com aviso explícito de que não é causalidade.
2. **Nunca inventar dado** — ausência de dado é um estado visível ("Dado ainda não disponível"), nunca um placeholder, estimativa não rotulada ou zero.
3. **Toda métrica é rastreável** — fonte, URL da fonte e metodologia visíveis a partir de qualquer número exibido.
4. **Correção é auditável, não silenciosa** — qualquer mudança em valor já publicado vira uma revisão registrada, com motivo.
5. **Simples o bastante para um leigo, rigoroso o bastante para ser citável** — a mesma página serve o cidadão comum e o jornalista que vai citar o número.

## Accessibility & Inclusion

Padrão confirmado: WCAG 2.1 AA (já auditado nas fases anteriores do projeto — contraste de cor, foco por teclado, `<dl>`/`<dt>`/`<dd>`, overflow horizontal). Mobile-first é requisito de produto, não só responsividade: o público primário (cidadão comum) acessa majoritariamente por celular.
