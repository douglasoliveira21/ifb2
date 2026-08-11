"""Especificação dos indicadores integrados na Fase 2.

Cada spec descreve tudo que o sync precisa: de onde buscar o dado (série
SGS do BCB), como normalizá-lo, e os metadados que alimentam
`indicator_definitions` / `indicator_methodologies` / `sources`.
"""
from dataclasses import dataclass

from app.models.indicator_definition import IndicatorCategory, IndicatorPolarity
from app.sync.ibge_client import SidraQuery


@dataclass(frozen=True)
class SourceSpec:
    key: str  # identifica a fonte de forma estável entre execuções do sync
    name: str
    url: str
    description: str


@dataclass(frozen=True)
class IndicatorSpec:
    slug: str
    name: str
    category: IndicatorCategory
    unit: str
    polarity: IndicatorPolarity
    description_what: str
    description_how: str
    update_frequency: str
    source: SourceSpec
    sgs_series_code: int
    resample_monthly: bool  # true para séries diárias (ex: Selic)
    methodology: str
    invert_sign: bool = False  # true quando a fonte usa convenção de sinal oposta à exibida


@dataclass(frozen=True)
class StaticIndicatorMeta:
    """Metadados de um indicador cuja busca não segue o padrão SGS/BCB (ex:
    PRODES/INPE) — usa um conector próprio em app/sync/run.py, mas os mesmos
    campos de `indicator_definitions`/`indicator_methodologies`."""

    slug: str
    name: str
    category: IndicatorCategory
    unit: str
    polarity: IndicatorPolarity
    description_what: str
    description_how: str
    update_frequency: str
    source: SourceSpec
    methodology: str


SOURCE_IBGE = SourceSpec(
    key="ibge",
    name="IBGE",
    url="https://www.ibge.gov.br/",
    description="Instituto Brasileiro de Geografia e Estatística.",
)

SOURCE_BCB = SourceSpec(
    key="bcb",
    name="Banco Central do Brasil",
    url="https://www.bcb.gov.br/",
    description="Banco Central do Brasil.",
)

SOURCE_INPE = SourceSpec(
    key="inpe",
    name="INPE",
    url="https://www.gov.br/inpe/",
    description="Instituto Nacional de Pesquisas Espaciais.",
)

INDICATORS: list[IndicatorSpec] = [
    IndicatorSpec(
        slug="desemprego",
        name="Taxa de desemprego",
        category=IndicatorCategory.EMPREGO_RENDA,
        unit="%",
        polarity=IndicatorPolarity.lower_is_better,
        description_what=(
            "Percentual de pessoas de 14 anos ou mais que estavam desocupadas "
            "(sem trabalho, mas disponíveis e procurando) na semana de referência "
            "da pesquisa, em relação à força de trabalho."
        ),
        description_how=(
            "Quanto menor, maior a proporção da força de trabalho que está ocupada. "
            "É uma média móvel trimestral — reflete o trimestre encerrado no mês de referência, "
            "não apenas o mês isolado."
        ),
        update_frequency="mensal",
        source=SOURCE_IBGE,
        sgs_series_code=24369,
        resample_monthly=False,
        methodology=(
            "# Metodologia — Taxa de desemprego\n\n"
            "Fonte primária: Pesquisa Nacional por Amostra de Domicílios Contínua (PNAD Contínua), "
            "produzida pelo IBGE. O IFB coleta os valores já consolidados através da série temporal "
            "24369 do SGS (Sistema Gerenciador de Séries Temporais) do Banco Central, que replica "
            "oficialmente o indicador do IBGE.\n\n"
            "O valor de cada mês é uma média móvel trimestral (ex: o dado de março refere-se ao "
            "trimestre janeiro–março). Revisões da série pelo IBGE são refletidas nas próximas "
            "sincronizações e registradas em `data_revisions`."
        ),
    ),
    IndicatorSpec(
        slug="ipca",
        name="IPCA — inflação em 12 meses",
        category=IndicatorCategory.ECONOMIA,
        unit="%",
        polarity=IndicatorPolarity.lower_is_better,
        description_what=(
            "Variação acumulada em 12 meses do Índice Nacional de Preços ao Consumidor Amplo (IPCA), "
            "o índice oficial de inflação do Brasil."
        ),
        description_how=(
            "Mede o quanto os preços de uma cesta de consumo de referência subiram no acumulado dos "
            "últimos 12 meses. Não é o mesmo que a meta de inflação (que é um alvo definido pelo CMN) "
            "nem que a variação de um único mês."
        ),
        update_frequency="mensal",
        source=SOURCE_IBGE,
        sgs_series_code=13522,
        resample_monthly=False,
        methodology=(
            "# Metodologia — IPCA (12 meses)\n\n"
            "Fonte primária: IBGE, Sistema Nacional de Índices de Preços ao Consumidor (SNIPC). "
            "O IFB coleta o valor acumulado em 12 meses através da série temporal 13522 do SGS/BCB, "
            "que replica oficialmente o indicador do IBGE.\n\n"
            "O IPCA é apurado mensalmente a partir de preços coletados em regiões metropolitanas e "
            "municípios selecionados. Valores passados podem ser revistos pelo IBGE; quando isso "
            "ocorre, a próxima sincronização do IFB registra a mudança em `data_revisions`."
        ),
    ),
    IndicatorSpec(
        slug="selic",
        name="Taxa Selic (meta)",
        category=IndicatorCategory.ECONOMIA,
        unit="%",
        polarity=IndicatorPolarity.neutral,
        description_what=(
            "Meta para a taxa básica de juros da economia brasileira, definida pelo Comitê de "
            "Política Monetária (Copom) do Banco Central."
        ),
        description_how=(
            "A Selic não tem direção 'boa' ou 'ruim' única — ela é um instrumento de política "
            "monetária usado para controlar a inflação, e seu efeito depende do contexto econômico. "
            "Por isso o IFB não classifica variações da Selic como melhora ou piora."
        ),
        update_frequency="mensal",
        source=SOURCE_BCB,
        sgs_series_code=432,
        resample_monthly=True,
        methodology=(
            "# Metodologia — Taxa Selic (meta)\n\n"
            "Fonte primária: Banco Central do Brasil, decisões do Copom. O IFB coleta a série "
            "temporal 432 do SGS/BCB, que traz a meta vigente para a Selic em cada data.\n\n"
            "A série do BCB é diária (a meta permanece constante entre reuniões do Copom). O IFB "
            "consolida um valor por mês — o último disponível no mês — para manter a granularidade "
            "comparável aos demais indicadores. Isso significa que uma mudança de meta no fim do mês "
            "é o valor que representa aquele mês inteiro nesta série."
        ),
    ),
    IndicatorSpec(
        slug="divida-pib",
        name="Dívida bruta do governo geral (% do PIB)",
        category=IndicatorCategory.CONTAS_PUBLICAS,
        unit="%",
        polarity=IndicatorPolarity.lower_is_better,
        description_what=(
            "Percentual que a dívida bruta do governo geral (União, estados e municípios, incluindo "
            "previdência) representa em relação ao PIB do país."
        ),
        description_how=(
            "Mede o tamanho do endividamento público em relação ao tamanho da economia. Não indica "
            "sozinho se o endividamento é sustentável — isso depende também da taxa de juros, do "
            "crescimento econômico e do prazo da dívida."
        ),
        update_frequency="mensal",
        source=SOURCE_BCB,
        sgs_series_code=13762,
        resample_monthly=False,
        methodology=(
            "# Metodologia — Dívida bruta do governo geral (% do PIB)\n\n"
            "Fonte primária: Banco Central do Brasil, Estatísticas Fiscais. O IFB coleta a série "
            "temporal 13762 do SGS/BCB.\n\n"
            "O indicador soma as dívidas de União, estados e municípios (incluindo o regime geral de "
            "previdência), na metodologia de compilação usada pelo BCB, e divide pelo PIB acumulado "
            "em 12 meses. Mudanças de metodologia do BCB ao longo do tempo podem gerar quebras na "
            "série; revisões de valores já publicados ficam registradas em `data_revisions`."
        ),
    ),
    IndicatorSpec(
        slug="rendimento-medio-real",
        name="Rendimento médio real habitual",
        category=IndicatorCategory.EMPREGO_RENDA,
        unit="R$",
        polarity=IndicatorPolarity.higher_is_better,
        description_what=(
            "Rendimento médio mensal real (já descontada a inflação) que as pessoas ocupadas "
            "recebem habitualmente em todos os trabalhos, segundo a PNAD Contínua."
        ),
        description_how=(
            "Como é um valor médio, pode ser afetado por mudanças na composição da força de "
            "trabalho — por exemplo, em 2020 o indicador subiu porque a pandemia eliminou "
            "proporcionalmente mais vagas de baixa renda, e não porque os salários em geral "
            "subiram. Compare sempre com a taxa de desemprego do mesmo período."
        ),
        update_frequency="mensal",
        source=SOURCE_IBGE,
        sgs_series_code=24382,
        resample_monthly=False,
        methodology=(
            "# Metodologia — Rendimento médio real habitual\n\n"
            "Fonte primária: Pesquisa Nacional por Amostra de Domicílios Contínua (PNAD Contínua), "
            "IBGE. O IFB coleta o valor através da série temporal 24382 do SGS/BCB, que replica "
            "oficialmente o indicador do IBGE.\n\n"
            "É uma média móvel trimestral, em reais já deflacionados. Por ser uma média, é sensível "
            "à composição do mercado de trabalho no período — quedas de emprego concentradas em "
            "faixas de renda específicas podem mover o indicador sem que o rendimento de ninguém, "
            "individualmente, tenha mudado."
        ),
    ),
    IndicatorSpec(
        slug="pib-mensal",
        name="PIB mensal (valores correntes)",
        category=IndicatorCategory.ECONOMIA,
        unit="R$ milhões",
        polarity=IndicatorPolarity.higher_is_better,
        description_what=(
            "Estimativa mensal do Produto Interno Bruto do Brasil, em valores correntes (sem "
            "ajuste pela inflação), calculada pelo Banco Central."
        ),
        description_how=(
            "É uma estimativa mensal do Banco Central, usada inclusive como referência para outros "
            "indicadores (como a Dívida/PIB) — não é o mesmo número que o PIB trimestral oficial "
            "divulgado pelo IBGE nas Contas Nacionais, que segue metodologia própria e é a referência "
            "definitiva. Por estar em valores correntes, parte do crescimento observado ao longo dos "
            "anos reflete apenas a inflação acumulada, não crescimento real da economia."
        ),
        update_frequency="mensal",
        source=SOURCE_BCB,
        sgs_series_code=4380,
        resample_monthly=False,
        methodology=(
            "# Metodologia — PIB mensal (valores correntes)\n\n"
            "Fonte: Banco Central do Brasil, série temporal 4380 do SGS — estimativa mensal do PIB "
            "em valores correntes, usada pelo próprio BCB como insumo para estatísticas fiscais "
            "(como a relação Dívida/PIB).\n\n"
            "Esta série é diferente do PIB trimestral oficial do IBGE (Sistema de Contas Nacionais "
            "Trimestrais), que segue metodologia própria e é a referência definitiva para o "
            "resultado da economia brasileira. O IFB usa a série do BCB aqui por sua granularidade "
            "mensal; a integração do PIB trimestral oficial do IBGE é um item futuro."
        ),
    ),
    IndicatorSpec(
        slug="resultado-primario",
        name="Resultado primário do governo central (12 meses)",
        category=IndicatorCategory.CONTAS_PUBLICAS,
        unit="% do PIB",
        polarity=IndicatorPolarity.neutral,
        description_what=(
            "Diferença entre receitas e despesas do governo federal e do Banco Central, sem contar "
            "os juros da dívida pública, acumulada nos últimos 12 meses e expressa como percentual "
            "do PIB. Positivo é superávit (arrecadou mais do que gastou, sem contar juros); "
            "negativo é déficit."
        ),
        description_how=(
            "O IFB não classifica superávit como 'melhora' nem déficit como 'piora' automaticamente: "
            "em uma recessão, um déficit primário maior pode ser uma resposta deliberada para "
            "sustentar a economia; em outros momentos, pode indicar deterioração fiscal. O contexto "
            "importa mais do que o sinal isolado."
        ),
        update_frequency="mensal",
        source=SOURCE_BCB,
        sgs_series_code=5783,
        resample_monthly=False,
        invert_sign=True,
        methodology=(
            "# Metodologia — Resultado primário do governo central (12 meses)\n\n"
            "Fonte: Banco Central do Brasil, Estatísticas Fiscais — Necessidade de Financiamento do "
            "Setor Público (NFSP), série temporal 5783 do SGS (\"NFSP sem desvalorização cambial "
            "(% PIB) - Fluxo acumulado em 12 meses - Resultado primário - Total - Governo Federal e "
            "Banco Central\").\n\n"
            "**Nota sobre o sinal:** o BCB publica esta série na convenção de NFSP, em que um valor "
            "positivo significa necessidade de financiamento (ou seja, déficit). O IFB inverte o "
            "sinal antes de exibir o dado, para usar a convenção mais comum em que positivo = "
            "superávit e negativo = déficit — a mesma usada pela imprensa e pelo Tesouro Nacional ao "
            "anunciar o resultado primário. Nenhum valor numérico é alterado além da troca de sinal; "
            "a transformação está documentada aqui e no código-fonte do sync."
        ),
    ),
    IndicatorSpec(
        slug="credito-total-sfn",
        name="Saldo da carteira de crédito do Sistema Financeiro Nacional",
        category=IndicatorCategory.ECONOMIA,
        unit="R$ milhões",
        polarity=IndicatorPolarity.neutral,
        description_what=(
            "Saldo total de todas as operações de crédito (empréstimos e financiamentos) "
            "concedidas por bancos e demais instituições financeiras a pessoas físicas e "
            "jurídicas no Brasil, em um determinado mês."
        ),
        description_how=(
            "Não é classificado como melhora/piora — crédito em expansão pode significar tanto "
            "uma economia aquecida quanto endividamento excessivo, dependendo do contexto (taxa "
            "de juros, inadimplência, renda das famílias). Compare sempre com o indicador de "
            "endividamento das famílias e com a Selic do mesmo período."
        ),
        update_frequency="mensal",
        source=SOURCE_BCB,
        sgs_series_code=20539,
        resample_monthly=False,
        methodology=(
            "# Metodologia — Saldo da carteira de crédito do SFN\n\n"
            "Fonte: Banco Central do Brasil, Estatísticas Monetárias e de Crédito, série temporal "
            "20539 do SGS — saldo total das operações de crédito do Sistema Financeiro Nacional "
            "(pessoas físicas e jurídicas, recursos livres e direcionados).\n\n"
            "É um saldo (estoque), não um fluxo mensal de novas concessões — reflete o total "
            "acumulado de operações em aberto no fim de cada mês."
        ),
    ),
    IndicatorSpec(
        slug="endividamento-familias",
        name="Endividamento das famílias",
        category=IndicatorCategory.ECONOMIA,
        unit="% da renda acumulada em 12 meses",
        polarity=IndicatorPolarity.lower_is_better,
        description_what=(
            "Relação entre o saldo total das dívidas das famílias com o Sistema Financeiro "
            "Nacional e a renda acumulada nos últimos 12 meses, com ajuste sazonal."
        ),
        description_how=(
            "Quanto maior, mais comprometida está a renda das famílias com dívidas já "
            "contraídas — não deve ser confundido com o comprometimento mensal de renda com o "
            "pagamento de dívidas (juros e amortizações), que é um indicador diferente do BCB."
        ),
        update_frequency="mensal",
        source=SOURCE_BCB,
        sgs_series_code=29034,
        resample_monthly=False,
        methodology=(
            "# Metodologia — Endividamento das famílias\n\n"
            "Fonte: Banco Central do Brasil, Estatísticas Monetárias e de Crédito, série temporal "
            "29034 do SGS — relação entre o saldo das dívidas das famílias com o SFN e a renda "
            "acumulada em 12 meses, com ajuste sazonal.\n\n"
            "O BCB revisa periodicamente a metodologia de cálculo da renda das famílias usada "
            "nesta série; revisões de valores já publicados ficam registradas em `data_revisions`."
        ),
    ),
    IndicatorSpec(
        slug="divida-liquida-setor-publico",
        name="Dívida líquida do setor público (% do PIB)",
        category=IndicatorCategory.CONTAS_PUBLICAS,
        unit="% do PIB",
        polarity=IndicatorPolarity.lower_is_better,
        description_what=(
            "Percentual que a dívida líquida do setor público (União, estados, municípios e "
            "Banco Central) representa em relação ao PIB — diferente da dívida bruta por "
            "descontar os ativos financeiros do setor público (reservas internacionais, "
            "créditos, aplicações), não só as obrigações."
        ),
        description_how=(
            "É um indicador complementar à dívida bruta (indicador `divida-pib`): a dívida "
            "líquida é sempre menor porque desconta os ativos do setor público, mas segue a "
            "mesma direção de leitura — quanto menor, mais espaço fiscal o país tem."
        ),
        update_frequency="mensal",
        source=SOURCE_BCB,
        sgs_series_code=4513,
        resample_monthly=False,
        methodology=(
            "# Metodologia — Dívida líquida do setor público (% do PIB)\n\n"
            "Fonte: Banco Central do Brasil, Estatísticas Fiscais. O IFB coleta a série "
            "temporal 4513 do SGS/BCB.\n\n"
            "Diferente da dívida bruta do governo geral (indicador `divida-pib`, série 13762), "
            "esta série cobre o setor público consolidado (incluindo o Banco Central) e desconta "
            "os ativos financeiros do setor público — por isso é sempre um número menor que a "
            "dívida bruta. Validado contra o valor amplamente noticiado de fechamento de 2020 "
            "(61,3% do PIB, alta puxada pelos gastos emergenciais da pandemia)."
        ),
    ),
]

DEFORESTATION_LEGAL_AMAZON = StaticIndicatorMeta(
    slug="desmatamento-amazonia-legal",
    name="Desmatamento — Amazônia Legal",
    category=IndicatorCategory.MEIO_AMBIENTE,
    unit="km²/ano",
    polarity=IndicatorPolarity.lower_is_better,
    description_what=(
        "Área total de floresta desmatada na Amazônia Legal em cada período PRODES (1º de agosto a "
        "31 de julho do ano seguinte), medida por satélite pelo INPE."
    ),
    description_how=(
        "O PRODES mede apenas corte raso (desmatamento total, não degradação florestal) e apenas "
        "áreas maiores que 6,25 hectares — desmatamentos menores não entram nesta série. O ano de "
        "referência usado aqui é o ano final do período de 12 meses (ex: o período de agosto/2020 a "
        "julho/2021 aparece como '2021')."
    ),
    update_frequency="anual",
    source=SOURCE_INPE,
    methodology=(
        "# Metodologia — Desmatamento na Amazônia Legal (PRODES)\n\n"
        "Fonte: INPE, Projeto de Monitoramento do Desmatamento na Amazônia Legal por Satélite "
        "(PRODES). O IFB coleta o arquivo de taxas anuais consolidadas publicado pelo painel oficial "
        "TerraBrasilis e soma as áreas de todos os estados da Amazônia Legal em cada período de 12 "
        "meses (1º de agosto a 31 de julho).\n\n"
        "O PRODES é a referência oficial do governo brasileiro para a taxa anual de desmatamento por "
        "corte raso na Amazônia Legal — não deve ser confundido com o DETER, um sistema de alertas "
        "rápidos (não oficiais para fins de taxa anual) usado para fiscalização em tempo quase real. "
        "Os valores somados pelo IFB foram conferidos contra números oficialmente divulgados (ex: o "
        "período 08/2020–07/2021 soma 13.038 km², o valor amplamente noticiado à época)."
    ),
)

ALFABETISMO = StaticIndicatorMeta(
    slug="taxa-analfabetismo",
    name="Taxa de analfabetismo (15 anos ou mais)",
    category=IndicatorCategory.EDUCACAO,
    unit="%",
    polarity=IndicatorPolarity.lower_is_better,
    description_what=(
        "Percentual de pessoas de 15 anos ou mais de idade que não sabem ler e escrever um "
        "bilhete simples, segundo a PNAD Contínua."
    ),
    description_how=(
        "Quanto menor, menor a proporção de adultos analfabetos. A série tem uma lacuna em "
        "2020–2021 porque a PNAD Contínua não coletou esse módulo durante a pandemia."
    ),
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Taxa de analfabetismo\n\n"
        "Fonte: IBGE, PNAD Contínua — tabela SIDRA 7113, variável 10267 (\"Taxa de "
        "analfabetismo das pessoas de 15 anos ou mais de idade\"), categoria Total (sexo) e "
        "15 anos ou mais (faixa etária).\n\n"
        "Não há levantamento para 2020 e 2021 — a pesquisa suspendeu esse módulo específico "
        "durante a pandemia. O IFB mostra a série como ela é, com a lacuna, em vez de "
        "interpolar um valor que a fonte não produziu."
    ),
)
ALFABETISMO_QUERY = SidraQuery(table=7113, variable=10267, classifications={2: 6794, 58: 2795})

ESPERANCA_VIDA = StaticIndicatorMeta(
    slug="esperanca-de-vida",
    name="Esperança de vida ao nascer",
    category=IndicatorCategory.SAUDE,
    unit="anos",
    polarity=IndicatorPolarity.higher_is_better,
    description_what=(
        "Número médio de anos que uma pessoa nascida em determinado ano viveria, se as condições "
        "de mortalidade daquele ano se mantivessem constantes ao longo de toda a vida dela."
    ),
    description_how=(
        "Quanto maior, melhor — reflete avanços em saúde, saneamento e condições de vida "
        "acumulados ao longo de décadas, não uma política de um único ano."
    ),
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Esperança de vida ao nascer\n\n"
        "Fonte: IBGE, Projeção da População do Brasil — tabela SIDRA 7362, variável 2503, "
        "categoria Total (sexo).\n\n"
        "**Importante**: este número vem do modelo oficial de projeção demográfica do IBGE, não "
        "de uma contagem direta de óbitos a cada ano — é a referência padrão usada oficialmente "
        "no Brasil para esperança de vida, inclusive para anos recentes, porque estimar esse "
        "indicador a partir de registro civil bruto tem defasagem de vários anos. O IFB sincroniza "
        "apenas os anos já decorridos: o modelo do IBGE projeta até 2060, mas mostrar um ano "
        "futuro como se fosse um valor observado violaria o princípio de nunca apresentar dado "
        "que não é real."
    ),
)
ESPERANCA_VIDA_QUERY = SidraQuery(table=7362, variable=2503, classifications={2: 6794, 1933: "all"})

MORTALIDADE_INFANTIL = StaticIndicatorMeta(
    slug="mortalidade-infantil",
    name="Mortalidade infantil",
    category=IndicatorCategory.SAUDE,
    unit="por mil nascidos vivos",
    polarity=IndicatorPolarity.lower_is_better,
    description_what=(
        "Número estimado de óbitos de crianças menores de 1 ano de idade para cada mil nascidos "
        "vivos, em determinado ano."
    ),
    description_how="Quanto menor, melhor.",
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Mortalidade infantil\n\n"
        "Fonte: IBGE, Projeção da População do Brasil — tabela SIDRA 7362, variável 1940, "
        "categoria Total (sexo).\n\n"
        "**Importante**: assim como a esperança de vida (mesma tabela), este número vem do "
        "modelo oficial de projeção demográfica do IBGE — a referência padrão usada oficialmente "
        "no Brasil, inclusive para anos recentes, já que a apuração direta pelo registro civil "
        "tem defasagem de vários anos. O IFB sincroniza apenas os anos já decorridos, nunca um "
        "ano projetado como se fosse observado."
    ),
)
MORTALIDADE_INFANTIL_QUERY = SidraQuery(table=7362, variable=1940, classifications={2: 6794, 1933: "all"})

PIB_PER_CAPITA = StaticIndicatorMeta(
    slug="pib-per-capita",
    name="PIB per capita (valores correntes)",
    category=IndicatorCategory.ECONOMIA,
    unit="R$",
    polarity=IndicatorPolarity.higher_is_better,
    description_what=(
        "Produto Interno Bruto dividido pela população residente estimada, em reais correntes "
        "(sem ajuste pela inflação) — quanto a economia produziu, em média, por habitante."
    ),
    description_how=(
        "Por estar em valores correntes, parte do crescimento observado ao longo dos anos "
        "reflete apenas a inflação acumulada, não necessariamente mais produção ou renda real "
        "por pessoa. É também uma média — não mostra como a renda é distribuída entre as "
        "pessoas."
    ),
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — PIB per capita (valores correntes)\n\n"
        "Fonte: IBGE, Sistema de Contas Nacionais (Contas Nacionais Anuais) — tabela SIDRA 6784, "
        "variável 9812 (\"PIB per capita - valores correntes\").\n\n"
        "Esta é a referência oficial e definitiva de PIB per capita do Brasil, calculada pelo "
        "IBGE dividindo o PIB anual pela população residente estimada para o mesmo ano. Como as "
        "Contas Nacionais Anuais têm um processo de fechamento mais longo que os indicadores "
        "mensais, o ano mais recente disponível costuma ficar de um a dois anos atrás do ano "
        "corrente."
    ),
)
PIB_PER_CAPITA_QUERY = SidraQuery(table=6784, variable=9812, classifications={})

SOURCE_INEP = SourceSpec(
    key="inep",
    name="INEP",
    url="https://www.gov.br/inep/",
    description="Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira.",
)

_IDEB_ZIP_URL = "https://download.inep.gov.br/ideb/resultados/divulgacao_brasil_ideb_2025.zip"

_IDEB_METHODOLOGY_INTRO = (
    "Fonte: INEP, divulgação de resultados do IDEB (Índice de Desenvolvimento da Educação "
    "Básica) — planilha oficial `divulgacao_brasil_ideb_2025.zip`, aba \"{sheet}\", linha "
    "\"Total\" (todas as redes de ensino somadas).\n\n"
    "**Como é calculado**: o IDEB combina a taxa de aprovação (Censo Escolar) com a média de "
    "desempenho em português e matemática no SAEB, em uma escala de 0 a 10. Não é uma nota de "
    "prova isolada — uma rede pode ter nota alta no SAEB e IDEB baixo se a taxa de aprovação for "
    "ruim (ou vice-versa).\n\n"
    "**Periodicidade**: o IDEB é apurado apenas em anos ímpares (a cada 2 anos), acompanhando o "
    "ciclo do Censo Escolar e do SAEB — não há dado para anos pares.\n\n"
    "**Sem API**: diferente das demais fontes do IFB, o INEP não publica os resultados do IDEB "
    "em uma API — apenas como planilha para download, uma edição por vez. O IFB baixa e lê essa "
    "planilha diretamente; a URL é específica da edição 2025 e precisará ser atualizada "
    "manualmente no código-fonte quando o INEP publicar a próxima edição (normalmente a cada 2 "
    "anos)."
)

IDEB_ANOS_INICIAIS = StaticIndicatorMeta(
    slug="ideb-anos-iniciais",
    name="IDEB — Anos Iniciais do Ensino Fundamental",
    category=IndicatorCategory.EDUCACAO,
    unit="pontos (0–10)",
    polarity=IndicatorPolarity.higher_is_better,
    description_what=(
        "Índice de Desenvolvimento da Educação Básica (IDEB) para os Anos Iniciais do Ensino "
        "Fundamental (1º ao 5º ano), somando todas as redes de ensino do Brasil."
    ),
    description_how=(
        "Quanto maior, melhor — combina aprendizado (SAEB) e fluxo escolar (taxa de aprovação). "
        "Apurado só em anos ímpares; 2021 registrou queda em relação a 2019 por causa do impacto "
        "da pandemia na aprendizagem."
    ),
    update_frequency="a cada 2 anos",
    source=SOURCE_INEP,
    methodology="# Metodologia — IDEB, Anos Iniciais do Ensino Fundamental\n\n"
    + _IDEB_METHODOLOGY_INTRO.format(sheet="Brasil (Anos Iniciais)"),
)

IDEB_ANOS_FINAIS = StaticIndicatorMeta(
    slug="ideb-anos-finais",
    name="IDEB — Anos Finais do Ensino Fundamental",
    category=IndicatorCategory.EDUCACAO,
    unit="pontos (0–10)",
    polarity=IndicatorPolarity.higher_is_better,
    description_what=(
        "Índice de Desenvolvimento da Educação Básica (IDEB) para os Anos Finais do Ensino "
        "Fundamental (6º ao 9º ano), somando todas as redes de ensino do Brasil."
    ),
    description_how=(
        "Quanto maior, melhor. Historicamente mais baixo e mais estagnado que os Anos Iniciais — "
        "é o segmento em que o Brasil tem mais dificuldade de avançar."
    ),
    update_frequency="a cada 2 anos",
    source=SOURCE_INEP,
    methodology="# Metodologia — IDEB, Anos Finais do Ensino Fundamental\n\n"
    + _IDEB_METHODOLOGY_INTRO.format(sheet="Brasil (Anos Finais)"),
)

IDEB_ENSINO_MEDIO = StaticIndicatorMeta(
    slug="ideb-ensino-medio",
    name="IDEB — Ensino Médio",
    category=IndicatorCategory.EDUCACAO,
    unit="pontos (0–10)",
    polarity=IndicatorPolarity.higher_is_better,
    description_what=(
        "Índice de Desenvolvimento da Educação Básica (IDEB) para o Ensino Médio, somando todas "
        "as redes de ensino do Brasil."
    ),
    description_how=(
        "Quanto maior, melhor. É o segmento com a nota mais baixa entre as três etapas — o "
        "Ensino Médio só passou a ter meta e cálculo direto do IDEB a partir de 2017 nesta série "
        "consolidada."
    ),
    update_frequency="a cada 2 anos",
    source=SOURCE_INEP,
    methodology="# Metodologia — IDEB, Ensino Médio\n\n" + _IDEB_METHODOLOGY_INTRO.format(sheet="Brasil (EM)"),
)

IDEB_ZIP_URL = _IDEB_ZIP_URL

SOURCE_SICONFI = SourceSpec(
    key="siconfi",
    name="Tesouro Nacional (SICONFI)",
    url="https://siconfi.tesouro.gov.br/",
    description=(
        "Sistema de Informações Contábeis e Fiscais do Setor Público Brasileiro, mantido pela "
        "Secretaria do Tesouro Nacional."
    ),
)

SOURCE_TESOURO_TRANSFERENCIAS = SourceSpec(
    key="tesouro-transferencias-constitucionais",
    name="Tesouro Nacional — Transferências Constitucionais",
    url="https://www.tesourotransparente.gov.br/ckan/dataset/api-de-transferencias-constitucionais",
    description=(
        "Secretaria do Tesouro Nacional — API de Transferências Constitucionais e Legais da "
        "União a estados e municípios."
    ),
)

_RGF_METHODOLOGY_NOTE = (
    "**Sobre a apuração**: o Relatório de Gestão Fiscal (RGF) é declarado pelo próprio ente "
    "federativo ao Tesouro Nacional a cada quadrimestre, conforme exigido pela Lei de "
    "Responsabilidade Fiscal (LRF). O IFB sincroniza sempre o fechamento do 3º quadrimestre "
    "(valor de todo o exercício) para o Poder Executivo estadual. Não há dado disponível no "
    "SICONFI para exercícios anteriores a 2015."
)

DIVIDA_CONSOLIDADA_LIQUIDA_ESTADUAL = StaticIndicatorMeta(
    slug="divida-consolidada-liquida-estadual",
    name="Dívida consolidada líquida (% da RCL)",
    category=IndicatorCategory.CONTAS_PUBLICAS,
    unit="% da RCL ajustada",
    polarity=IndicatorPolarity.lower_is_better,
    description_what=(
        "Dívida Consolidada Líquida (DCL) do governo estadual — dívida consolidada menos "
        "disponibilidade de caixa e outros haveres financeiros — como percentual da Receita "
        "Corrente Líquida (RCL) ajustada do estado."
    ),
    description_how=(
        "A Lei de Responsabilidade Fiscal define um limite de 200% da RCL ajustada para "
        "estados. Quanto menor o percentual, menor o peso da dívida líquida em relação à "
        "arrecadação do estado. Estados que renegociaram dívidas antigas com a União nos anos "
        "1990 (como SP, RJ e MG) tendem a ter percentuais estruturalmente mais altos, "
        "independentemente da gestão fiscal recente."
    ),
    update_frequency="anual",
    source=SOURCE_SICONFI,
    methodology=(
        "# Metodologia — Dívida consolidada líquida estadual (% da RCL)\n\n"
        "Fonte: Tesouro Nacional, SICONFI — Relatório de Gestão Fiscal (RGF), Anexo 02 "
        "(Demonstrativo da Dívida Consolidada Líquida), conta \"% da DCL sobre a RCL Ajustada\", "
        "coluna do fechamento do 3º quadrimestre.\n\n" + _RGF_METHODOLOGY_NOTE
    ),
)

DESPESA_COM_PESSOAL_ESTADUAL = StaticIndicatorMeta(
    slug="despesa-com-pessoal-estadual",
    name="Despesa com pessoal (% da RCL)",
    category=IndicatorCategory.CONTAS_PUBLICAS,
    unit="% da RCL ajustada",
    polarity=IndicatorPolarity.lower_is_better,
    description_what=(
        "Despesa Total com Pessoal (DTP) do Poder Executivo estadual — folha de ativos, "
        "inativos e pensionistas, líquida de deduções previstas em lei — como percentual da "
        "Receita Corrente Líquida (RCL) ajustada do estado."
    ),
    description_how=(
        "A Lei de Responsabilidade Fiscal define, para o Poder Executivo estadual, limite "
        "máximo de 49% da RCL ajustada, limite prudencial de 46,55% (95% do máximo) e limite de "
        "alerta de 44,1% (90% do máximo). Ultrapassar o limite máximo obriga o governo a "
        "reduzir a despesa nos quadrimestres seguintes, sob pena de sanções previstas em lei."
    ),
    update_frequency="anual",
    source=SOURCE_SICONFI,
    methodology=(
        "# Metodologia — Despesa com pessoal estadual (% da RCL)\n\n"
        "Fonte: Tesouro Nacional, SICONFI — Relatório de Gestão Fiscal (RGF), Anexo 01 "
        "(Demonstrativo da Despesa com Pessoal), conta \"Despesa Total com Pessoal - DTP\", "
        "coluna \"% sobre a RCL Ajustada\", Poder Executivo, fechamento do 3º quadrimestre.\n\n"
        + _RGF_METHODOLOGY_NOTE
    ),
)

_TAXA_ESCOLARIZACAO_METHODOLOGY = (
    "Fonte: IBGE, PNAD Contínua — tabela SIDRA 7138, variável 10276 (\"Taxa de "
    "escolarização\"), categoria Total (sexo), grupo de idade \"{faixa}\".\n\n"
    "Mede o percentual de pessoas nessa faixa etária que frequentava escola ou creche na "
    "semana de referência da pesquisa, independentemente da série/ano cursado. Disponível por "
    "Brasil e por UF."
)

TAXA_ESCOLARIZACAO_6_A_14 = StaticIndicatorMeta(
    slug="taxa-escolarizacao-6-14",
    name="Taxa de escolarização (6 a 14 anos)",
    category=IndicatorCategory.EDUCACAO,
    unit="%",
    polarity=IndicatorPolarity.higher_is_better,
    description_what=(
        "Percentual de crianças e adolescentes de 6 a 14 anos (idade do Ensino Fundamental "
        "obrigatório) que frequentavam escola ou creche na semana de referência da pesquisa."
    ),
    description_how=(
        "Quanto maior, melhor — no Brasil este indicador já está perto da universalização "
        "(acima de 97% em quase todos os estados), então diferenças pequenas entre estados "
        "ainda são relevantes."
    ),
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology="# Metodologia — Taxa de escolarização (6 a 14 anos)\n\n"
    + _TAXA_ESCOLARIZACAO_METHODOLOGY.format(faixa="6 a 14 anos"),
)
TAXA_ESCOLARIZACAO_6_A_14_QUERY = SidraQuery(table=7138, variable=10276, classifications={2: 6794, 58: 31615})

TAXA_ESCOLARIZACAO_15_A_17 = StaticIndicatorMeta(
    slug="taxa-escolarizacao-15-17",
    name="Taxa de escolarização (15 a 17 anos)",
    category=IndicatorCategory.EDUCACAO,
    unit="%",
    polarity=IndicatorPolarity.higher_is_better,
    description_what=(
        "Percentual de adolescentes de 15 a 17 anos (idade do Ensino Médio) que frequentavam "
        "escola ou creche na semana de referência da pesquisa."
    ),
    description_how=(
        "Quanto maior, melhor. É consistentemente mais baixo que a taxa de 6 a 14 anos em todo "
        "o Brasil — reflete a evasão escolar que se concentra na transição para o Ensino Médio, "
        "e varia mais entre estados do que a escolarização no Ensino Fundamental."
    ),
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology="# Metodologia — Taxa de escolarização (15 a 17 anos)\n\n"
    + _TAXA_ESCOLARIZACAO_METHODOLOGY.format(faixa="15 a 17 anos"),
)
TAXA_ESCOLARIZACAO_15_A_17_QUERY = SidraQuery(table=7138, variable=10276, classifications={2: 6794, 58: 2792})

RECEITA_TOTAL_REALIZADA_ESTADUAL = StaticIndicatorMeta(
    slug="receita-total-realizada-estadual",
    name="Receita total realizada",
    category=IndicatorCategory.CONTAS_PUBLICAS,
    unit="R$",
    polarity=IndicatorPolarity.neutral,
    description_what=(
        "Total de receitas efetivamente arrecadadas pelo governo estadual em um ano — impostos, "
        "taxas, transferências recebidas e demais receitas orçamentárias, exceto operações "
        "intra-orçamentárias."
    ),
    description_how=(
        "O IFB não classifica este indicador como 'melhora' ou 'piora': um valor mais alto "
        "reflete o tamanho do orçamento do estado (população, atividade econômica, "
        "transferências recebidas), não necessariamente melhor gestão. Serve principalmente "
        "como referência de escala para comparar outros números de contas públicas do mesmo "
        "estado (ex: quanto a dívida ou a despesa com pessoal representam frente ao "
        "orçamento total)."
    ),
    update_frequency="anual",
    source=SOURCE_SICONFI,
    methodology=(
        "# Metodologia — Receita total realizada estadual\n\n"
        "Fonte: Tesouro Nacional, SICONFI — Relatório Resumido da Execução Orçamentária (RREO), "
        "Anexo 01 (Balanço Orçamentário), conta \"TOTAL DAS RECEITAS\", coluna \"Até o "
        "Bimestre\" (acumulado no ano), fechamento do 6º bimestre.\n\n"
        "**Sobre a apuração**: o RREO é declarado pelo próprio ente federativo ao Tesouro "
        "Nacional a cada bimestre, conforme exigido pela Lei de Responsabilidade Fiscal (LRF). "
        "O IFB sincroniza sempre o fechamento do 6º bimestre (valor acumulado de todo o "
        "exercício), consolidado para o governo estadual como um todo (não separado por "
        "poder). Não há dado disponível no SICONFI para exercícios anteriores a 2015."
    ),
)

TRANSFERENCIAS_CONSTITUCIONAIS_ESTADUAL = StaticIndicatorMeta(
    slug="transferencias-constitucionais-estadual",
    name="Transferências constitucionais recebidas pelo estado",
    category=IndicatorCategory.CONTAS_PUBLICAS,
    unit="R$",
    polarity=IndicatorPolarity.neutral,
    description_what=(
        "Total de transferências constitucionais e legais da União recebidas pelo governo "
        "estadual em um ano — soma do Fundo de Participação dos Estados (FPE), FUNDEB, "
        "royalties (petróleo, Itaipu, recursos hídricos e minerais), IPI-Exportação, Lei "
        "Kandir, CIDE-Combustíveis e demais repasses obrigatórios previstos em lei."
    ),
    description_how=(
        "O IFB não classifica este indicador como 'melhora' ou 'piora': um valor mais alto "
        "pode refletir mais população, mais atividade econômica (royalties, IPI-Exportação) ou "
        "mudanças no critério de partilha entre exercícios — não é, isoladamente, uma medida de "
        "desempenho de gestão estadual. Estados com economia menos diversificada tendem a "
        "depender proporcionalmente mais dessas transferências do que estados com arrecadação "
        "própria maior."
    ),
    update_frequency="anual",
    source=SOURCE_TESOURO_TRANSFERENCIAS,
    methodology=(
        "# Metodologia — Transferências constitucionais recebidas pelo estado\n\n"
        "Fonte: Secretaria do Tesouro Nacional, API de Transferências Constitucionais "
        "(`apiapex.tesouro.gov.br`), endpoint `por_estados`, somando o valor de todas as "
        "modalidades de transferência (FPE, FUNDEB, royalties, IPI-Exportação, Lei Kandir, "
        "CIDE-Combustíveis, IOF-Ouro e demais listadas pelo Tesouro) por estado e ano.\n\n"
        "Não inclui convênios, emendas parlamentares nem outras transferências discricionárias "
        "— apenas repasses obrigatórios previstos na Constituição ou em lei específica. O ano de "
        "referência é o ano de competência do repasse, não a data de pagamento."
    ),
)

SOURCE_CNES = SourceSpec(
    key="cnes",
    name="Ministério da Saúde (CNES)",
    url="https://dadosabertos.saude.gov.br/dataset/hospitais-e-leitos",
    description="Cadastro Nacional de Estabelecimentos de Saúde, Ministério da Saúde.",
)

LEITOS_SUS_ESTADUAL = StaticIndicatorMeta(
    slug="leitos-sus-estadual",
    name="Leitos SUS",
    category=IndicatorCategory.SAUDE,
    unit="leitos",
    polarity=IndicatorPolarity.higher_is_better,
    description_what=(
        "Número total de leitos hospitalares disponíveis para o SUS (Sistema Único de Saúde) "
        "no estado, somando todos os estabelecimentos cadastrados no CNES."
    ),
    description_how=(
        "Quanto maior, mais capacidade de internação disponível pelo SUS — mas o número bruto "
        "não leva em conta o tamanho da população do estado; para comparar estados de tamanhos "
        "diferentes, o ideal é olhar também a população de cada um. Não inclui leitos "
        "exclusivamente privados (fora do SUS)."
    ),
    update_frequency="anual",
    source=SOURCE_CNES,
    methodology=(
        "# Metodologia — Leitos SUS por estado\n\n"
        "Fonte: Ministério da Saúde, Cadastro Nacional de Estabelecimentos de Saúde (CNES) — "
        "arquivo anual `Leitos_AAAA.csv`, publicado em "
        "https://dadosabertos.saude.gov.br/dataset/hospitais-e-leitos. O IFB soma a coluna "
        "`LEITOS_SUS` de todos os estabelecimentos de cada estado, no último mês disponível de "
        "cada arquivo (normalmente dezembro; arquivos do ano corrente podem ter só os meses já "
        "publicados, dado o atraso normal do CNES).\n\n"
        "**Por que não a API do Ministério da Saúde**: a API pública de dados abertos do "
        "Ministério da Saúde (`apidadosabertos.saude.gov.br`) tem um filtro por UF que retorna "
        "erro 500 de forma consistente, e sua paginação não termina de forma sensata "
        "(testado até 5 milhões de registros implícitos, quando o Brasil tem cerca de 7 mil "
        "hospitais) — por isso o IFB usa os arquivos CSV estáticos publicados no mesmo portal, "
        "mais estáveis, em vez de depender dessa API."
    ),
)

SOURCE_FBSP = SourceSpec(
    key="fbsp",
    name="Fórum Brasileiro de Segurança Pública (FBSP)",
    url="https://forumseguranca.org.br/",
    description=(
        "Associação civil sem fins lucrativos que consolida e audita anualmente os dados de "
        "segurança pública enviados pelas Secretarias estaduais ao Sinesp. NÃO é um órgão do "
        "governo federal — é a única fonte não-governamental usada pelo IFB, adotada porque o "
        "sistema oficial (Sinesp/MJSP) não tem, hoje, um canal de acesso programático "
        "funcional (ver metodologia do indicador)."
    ),
)

TAXA_MORTES_VIOLENTAS_INTENCIONAIS_ESTADUAL = StaticIndicatorMeta(
    slug="taxa-mortes-violentas-intencionais-estadual",
    name="Taxa de Mortes Violentas Intencionais (MVI)",
    category=IndicatorCategory.SEGURANCA,
    unit="por 100 mil habitantes",
    polarity=IndicatorPolarity.lower_is_better,
    description_what=(
        "Soma de homicídio doloso, latrocínio (roubo seguido de morte), lesão corporal seguida "
        "de morte e mortes decorrentes de intervenção policial, por 100 mil habitantes — o "
        "indicador mais abrangente de violência letal intencional usado no Brasil, definido "
        "pelo Fórum Brasileiro de Segurança Pública."
    ),
    description_how=(
        "Quanto menor, melhor. É uma taxa (por 100 mil habitantes), não um número absoluto — "
        "permite comparar estados de tamanhos diferentes diretamente."
    ),
    update_frequency="anual",
    source=SOURCE_FBSP,
    methodology=(
        "# Metodologia — Taxa de Mortes Violentas Intencionais (MVI) por estado\n\n"
        "**Fonte não-governamental — leia com atenção**: este é o único indicador do IFB que "
        "não vem de um órgão público. Os números são declarados pelas Secretarias de Segurança "
        "Pública de cada estado ao Sinesp (Sistema Nacional de Estatísticas de Segurança "
        "Pública, Ministério da Justiça e Segurança Pública), mas o IFB os obtém já "
        "consolidados e auditados na planilha pública do Anuário Brasileiro de Segurança "
        "Pública (Fórum Brasileiro de Segurança Pública — FBSP), tabela \"Mortes violentas "
        "intencionais\", coluna \"Taxa (por 100 mil habitantes)\".\n\n"
        "**Por que não a fonte oficial diretamente**: o sistema do Ministério da Justiça e "
        "Segurança Pública para consulta desses dados (`dados.mj.gov.br`) está com o domínio "
        "fora do ar (não resolve mais por DNS). O portal que o substituiu "
        "(`dados.gov.br`) expõe os metadados do conjunto de dados sem exigir login, mas o "
        "download de qualquer arquivo exige autenticação — testado e confirmado (erro 401 "
        "mesmo navegando sem bloqueio de conteúdo). Até que uma dessas fontes primárias volte "
        "a funcionar, o IFB usa o FBSP, mantendo a fonte real sempre visível (nunca "
        "apresentada como \"dado oficial do governo\").\n\n"
        "**Sem série histórica automática**: o FBSP publica uma planilha por edição anual do "
        "Anuário, sem API — cada edição nova exige atualizar manualmente a URL no código "
        "(mesmo padrão já usado para o IDEB/INEP). A edição vigente (2025) traz os anos 2023 "
        "e 2024."
    ),
)

# --- Piloto de granularidade municipal (Fase municipal) ---------------------
#
# Diferente dos indicadores estaduais (27 UFs, histórico completo desde
# 2015), os municipais trazem só o último ano completo disponível — o
# volume de ~5.570 municípios torna inviável buscar anos anteriores numa
# sync diária (ver docstrings de `fetch_transferencias_constitucionais_by_municipio`
# em `tesouro_transferencias_client.py` e `fetch_rgf_by_municipio` em
# `siconfi_client.py`).

TRANSFERENCIAS_CONSTITUCIONAIS_MUNICIPAL = StaticIndicatorMeta(
    slug="transferencias-constitucionais-municipal",
    name="Transferências constitucionais recebidas pelo município",
    category=IndicatorCategory.CONTAS_PUBLICAS,
    unit="R$",
    polarity=IndicatorPolarity.neutral,
    description_what=(
        "Total de transferências constitucionais e legais da União recebidas pela prefeitura "
        "no último ano completo — FPM, FUNDEB, royalties, ITR, IPI-Exportação, Lei Kandir, "
        "CIDE-Combustíveis e demais repasses obrigatórios previstos em lei."
    ),
    description_how=(
        "O IFB não classifica este indicador como 'melhora' ou 'piora' — reflete o tamanho da "
        "população e da economia local, não desempenho de gestão. Diferente do indicador "
        "estadual (que tem série histórica completa desde 2015), o municipal traz só o último "
        "ano completo disponível — ver metodologia."
    ),
    update_frequency="anual",
    source=SOURCE_TESOURO_TRANSFERENCIAS,
    methodology=(
        "# Metodologia — Transferências constitucionais recebidas pelo município\n\n"
        "Fonte: Secretaria do Tesouro Nacional, API de Transferências Constitucionais "
        "(`apiapex.tesouro.gov.br`), endpoint `por_estado_municipio`, somando o valor de todas "
        "as modalidades de transferência por município no ano.\n\n"
        "**Só o último ano completo, não série histórica**: o endpoint não tem busca em lote "
        "por município (diferente do endpoint por estado) — uma única consulta por estado já "
        "retorna todos os seus municípios, mas em nível bem mais granular (ex: São Paulo/2023 "
        "sozinho soma ~40 mil linhas, uma por município × mês × modalidade). Buscar vários "
        "anos multiplicaria esse volume proporcionalmente; por ora, o IFB sincroniza só o "
        "último ano completo (o ano corrente é sempre parcial)."
    ),
)

DESPESA_COM_PESSOAL_MUNICIPAL = StaticIndicatorMeta(
    slug="despesa-com-pessoal-municipal",
    name="Despesa com pessoal (% da RCL) — município",
    category=IndicatorCategory.CONTAS_PUBLICAS,
    unit="% da RCL ajustada",
    polarity=IndicatorPolarity.lower_is_better,
    description_what=(
        "Despesa Total com Pessoal (DTP) da prefeitura — folha de ativos, inativos e "
        "pensionistas, líquida de deduções previstas em lei — como percentual da Receita "
        "Corrente Líquida (RCL) ajustada do município, no último ano completo."
    ),
    description_how=(
        "A Lei de Responsabilidade Fiscal define, para o Poder Executivo municipal, limite "
        "máximo de 54% da RCL ajustada (diferente do limite estadual, 49%). Ultrapassar o "
        "limite obriga o governo a reduzir a despesa nos quadrimestres seguintes."
    ),
    update_frequency="anual",
    source=SOURCE_SICONFI,
    methodology=(
        "# Metodologia — Despesa com pessoal municipal (% da RCL)\n\n"
        "Fonte: Tesouro Nacional, SICONFI — Relatório de Gestão Fiscal (RGF), Anexo 01, conta "
        "\"Despesa Total com Pessoal - DTP\", coluna \"% sobre a RCL Ajustada\", Poder "
        "Executivo, fechamento do 3º quadrimestre, `id_ente` = código IBGE de 7 dígitos do "
        "município.\n\n"
        "**Só o último ano completo**: o SICONFI não tem endpoint em lote por município — é "
        "uma requisição HTTP por município (~5.570 no total), buscada em paralelo mas ainda "
        "assim inviável de repetir para cada um dos ~10 anos disponíveis numa sync diária. "
        "Testado contra São Paulo (capital) em 2023: 29,98% da RCL, dentro do limite de 54%."
    ),
)

# --- Demografia (IBGE, tabelas 6579 e 7360) ---------------------------------
#
# Reaproveita 100% o cliente SIDRA já existente (`fetch_sidra_series`,
# `fetch_sidra_series_by_state`, `drop_future_years`) — mesmo padrão de
# ESPERANCA_VIDA/MORTALIDADE_INFANTIL, só tabelas/variáveis diferentes.
# Tabela 7360 tem a mesma armadilha de "dois campos Ano" já documentada
# para a 7362 (`_extract_year` em ibge_client.py já trata isso).
#
# Valores conferidos contra números amplamente divulgados: população do
# Brasil em 2025 = 213.421.037 (mesmo valor da estimativa IBGE noticiada);
# taxa de fecundidade total 2023 = 1,75 filho/mulher (abaixo do nível de
# reposição, número muito citado na imprensa); taxa de crescimento
# geométrico 2023 = 0,68% (crescimento populacional em desaceleração,
# também amplamente noticiado); índice de envelhecimento mais baixo nos
# estados do Norte (ex: Amazonas ~20 em 2023) que no Sul, batendo com o
# padrão demográfico regional conhecido.

POPULACAO_RESIDENTE = StaticIndicatorMeta(
    slug="populacao-residente",
    name="População residente estimada",
    category=IndicatorCategory.DEMOGRAFIA,
    unit="pessoas",
    polarity=IndicatorPolarity.neutral,
    description_what="Estimativa da população residente, atualizada anualmente pelo IBGE.",
    description_how=(
        "Não é um indicador de 'melhora' ou 'piora' — é o tamanho da população, usado como "
        "referência para calcular outros indicadores per capita."
    ),
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — População residente estimada\n\n"
        "Fonte: IBGE, Estimativas de População — tabela SIDRA 6579, variável 9324."
    ),
)
POPULACAO_RESIDENTE_QUERY = SidraQuery(table=6579, variable=9324, classifications={})

NASCIMENTOS = StaticIndicatorMeta(
    slug="nascimentos",
    name="Nascimentos",
    category=IndicatorCategory.DEMOGRAFIA,
    unit="nascimentos",
    polarity=IndicatorPolarity.neutral,
    description_what="Número estimado de nascimentos no ano, segundo a Projeção da População do IBGE.",
    description_how="Não é classificado como melhora/piora — é um número absoluto de referência.",
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Nascimentos\n\n"
        "Fonte: IBGE, Projeção da População — tabela SIDRA 7360, variável 10600 "
        "(\"Nascimentos\"), parte do modelo oficial de projeção demográfica, não contagem "
        "direta de registro civil (que tem defasagem de anos)."
    ),
)
NASCIMENTOS_QUERY = SidraQuery(table=7360, variable=10600, classifications={1933: "all"})

OBITOS = StaticIndicatorMeta(
    slug="obitos",
    name="Óbitos",
    category=IndicatorCategory.DEMOGRAFIA,
    unit="óbitos",
    polarity=IndicatorPolarity.neutral,
    description_what="Número estimado de óbitos no ano, segundo a Projeção da População do IBGE.",
    description_how=(
        "Não é classificado como melhora/piora automaticamente — o número tende a subir com o "
        "envelhecimento da população, o que não é, por si só, um resultado ruim de política "
        "pública."
    ),
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Óbitos\n\n"
        "Fonte: IBGE, Projeção da População — tabela SIDRA 7360, variável 10601 (\"Óbitos\"), "
        "modelo oficial de projeção demográfica."
    ),
)
OBITOS_QUERY = SidraQuery(table=7360, variable=10601, classifications={1933: "all"})

TAXA_CRESCIMENTO_POPULACIONAL = StaticIndicatorMeta(
    slug="taxa-crescimento-populacional",
    name="Taxa de crescimento populacional",
    category=IndicatorCategory.DEMOGRAFIA,
    unit="%",
    polarity=IndicatorPolarity.neutral,
    description_what="Taxa de crescimento geométrico anual da população, segundo o IBGE.",
    description_how=(
        "Não é classificada como melhora/piora — o Brasil está em desaceleração populacional "
        "estrutural (transição demográfica), não um resultado de política de um governo "
        "específico."
    ),
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Taxa de crescimento populacional\n\n"
        "Fonte: IBGE, Projeção da População — tabela SIDRA 7360, variável 10605 (\"Taxa de "
        "crescimento geométrico\")."
    ),
)
TAXA_CRESCIMENTO_POPULACIONAL_QUERY = SidraQuery(table=7360, variable=10605, classifications={1933: "all"})

TAXA_NATALIDADE = StaticIndicatorMeta(
    slug="taxa-natalidade",
    name="Taxa bruta de natalidade",
    category=IndicatorCategory.DEMOGRAFIA,
    unit="por mil habitantes",
    polarity=IndicatorPolarity.neutral,
    description_what="Número de nascimentos por mil habitantes no ano, segundo o IBGE.",
    description_how="Não é classificada como melhora/piora — reflete tendência demográfica, não política pública isolada.",
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Taxa bruta de natalidade\n\n"
        "Fonte: IBGE, Projeção da População — tabela SIDRA 7360, variável 10606."
    ),
)
TAXA_NATALIDADE_QUERY = SidraQuery(table=7360, variable=10606, classifications={1933: "all"})

TAXA_MORTALIDADE_GERAL = StaticIndicatorMeta(
    slug="taxa-mortalidade-geral",
    name="Taxa bruta de mortalidade",
    category=IndicatorCategory.DEMOGRAFIA,
    unit="por mil habitantes",
    polarity=IndicatorPolarity.neutral,
    description_what=(
        "Número de óbitos por mil habitantes no ano (todas as idades e causas) — diferente da "
        "mortalidade infantil, que mede só óbitos de crianças menores de 1 ano."
    ),
    description_how=(
        "O IFB não classifica este indicador como melhora/piora: ele tende a subir "
        "estruturalmente com o envelhecimento da população, mesmo com a saúde melhorando — "
        "diferente da mortalidade infantil (essa sim classificada, por ser um sinal mais "
        "direto de saúde pública). Compare sempre com a esperança de vida do mesmo período "
        "antes de interpretar uma alta como piora."
    ),
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Taxa bruta de mortalidade\n\n"
        "Fonte: IBGE, Projeção da População — tabela SIDRA 7360, variável 10607. Não confundir "
        "com mortalidade infantil (indicador separado, `mortalidade-infantil`)."
    ),
)
TAXA_MORTALIDADE_GERAL_QUERY = SidraQuery(table=7360, variable=10607, classifications={1933: "all"})

TAXA_FECUNDIDADE = StaticIndicatorMeta(
    slug="taxa-fecundidade",
    name="Taxa de fecundidade total",
    category=IndicatorCategory.DEMOGRAFIA,
    unit="filhos por mulher",
    polarity=IndicatorPolarity.neutral,
    description_what=(
        "Número médio de filhos que uma mulher teria ao final da vida reprodutiva, mantidas as "
        "taxas de fecundidade por idade observadas no ano."
    ),
    description_how=(
        "Não é classificada como melhora/piora — o Brasil está abaixo do nível de reposição "
        "populacional (2,1 filhos/mulher) desde a década de 2000, tendência estrutural de "
        "longo prazo."
    ),
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Taxa de fecundidade total\n\n"
        "Fonte: IBGE, Projeção da População — tabela SIDRA 7360, variável 2493."
    ),
)
TAXA_FECUNDIDADE_QUERY = SidraQuery(table=7360, variable=2493, classifications={1933: "all"})

INDICE_ENVELHECIMENTO = StaticIndicatorMeta(
    slug="indice-envelhecimento",
    name="Índice de envelhecimento",
    category=IndicatorCategory.DEMOGRAFIA,
    unit="%",
    polarity=IndicatorPolarity.neutral,
    description_what=(
        "Número de pessoas de 65 anos ou mais para cada 100 pessoas de 0 a 14 anos — quanto "
        "maior, mais envelhecida é a estrutura etária da população."
    ),
    description_how=(
        "Não é classificado como melhora/piora — reflete a transição demográfica (mais "
        "esperança de vida, menos nascimentos), com implicações para previdência e saúde que "
        "vão além de um único governo."
    ),
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Índice de envelhecimento\n\n"
        "Fonte: IBGE, Projeção da População — tabela SIDRA 7360, variável 10612."
    ),
)
INDICE_ENVELHECIMENTO_QUERY = SidraQuery(table=7360, variable=10612, classifications={1933: "all"})

PIB_VALORES_CORRENTES = StaticIndicatorMeta(
    slug="pib-valores-correntes",
    name="PIB (valores correntes)",
    category=IndicatorCategory.ECONOMIA,
    unit="R$ milhões",
    polarity=IndicatorPolarity.neutral,
    description_what=(
        "Produto Interno Bruto anual do Brasil, em valores correntes (sem ajuste pela "
        "inflação) — soma de tudo que foi produzido no país no ano, medido a preços do "
        "próprio ano."
    ),
    description_how=(
        "Não é classificado como melhora/piora isoladamente — parte do crescimento observado "
        "ao longo dos anos reflete apenas a inflação acumulada, não crescimento real da "
        "economia. Para avaliar crescimento real, use o indicador `crescimento-pib` (variação "
        "em volume, já descontada a inflação)."
    ),
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — PIB (valores correntes)\n\n"
        "Fonte: IBGE, Sistema de Contas Nacionais — tabela SIDRA 6784, variável 9808. É o PIB "
        "oficial anual do Brasil (Contas Nacionais Anuais), a referência definitiva para o "
        "resultado da economia — distinto da estimativa mensal do Banco Central usada no "
        "indicador `pib-mensal`, que segue metodologia própria e é atualizada com maior "
        "frequência, mas menor precisão."
    ),
)
PIB_VALORES_CORRENTES_QUERY = SidraQuery(table=6784, variable=9808, classifications={})

CRESCIMENTO_PIB = StaticIndicatorMeta(
    slug="crescimento-pib",
    name="Crescimento do PIB (variação real)",
    category=IndicatorCategory.ECONOMIA,
    unit="%",
    polarity=IndicatorPolarity.higher_is_better,
    description_what=(
        "Variação percentual do Produto Interno Bruto do Brasil em relação ao ano anterior, "
        "em volume — ou seja, já descontado o efeito da inflação. É a medida oficial de "
        "quanto a economia brasileira cresceu (ou encolheu) em cada ano."
    ),
    description_how=(
        "Positivo indica que a economia produziu mais bens e serviços do que no ano anterior; "
        "negativo indica recessão (como em 2020, com a pandemia). Não confundir com o PIB em "
        "valores correntes, que também sobe com a inflação mesmo sem crescimento real."
    ),
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Crescimento do PIB (variação real)\n\n"
        "Fonte: IBGE, Sistema de Contas Nacionais — tabela SIDRA 6784, variável 9810 (\"PIB — "
        "variação em volume\"). Compara o volume de bens e serviços produzidos em cada ano com "
        "o do ano anterior, a preços constantes — a mesma taxa amplamente divulgada como "
        "\"crescimento do PIB\" nos anúncios oficiais do IBGE."
    ),
)
CRESCIMENTO_PIB_QUERY = SidraQuery(table=6784, variable=9810, classifications={})

PIB_DEFLATOR = StaticIndicatorMeta(
    slug="pib-deflator",
    name="Deflator do PIB (variação anual)",
    category=IndicatorCategory.ECONOMIA,
    unit="%",
    polarity=IndicatorPolarity.neutral,
    description_what=(
        "Variação anual do deflator implícito do PIB — uma medida ampla de inflação que "
        "cobre todos os bens e serviços finais produzidos na economia, não apenas a cesta de "
        "consumo das famílias (como o IPCA)."
    ),
    description_how=(
        "Não é classificado como melhora/piora — é um indicador de contexto para interpretar "
        "a diferença entre o PIB em valores correntes e o PIB em volume. Difere do IPCA por "
        "medir a inflação de toda a produção do país (incluindo investimentos e exportações), "
        "não só o que as famílias compram."
    ),
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Deflator do PIB (variação anual)\n\n"
        "Fonte: IBGE, Sistema de Contas Nacionais — tabela SIDRA 6784, variável 9811. Calculado "
        "pelo próprio IBGE como a razão entre o PIB a preços correntes e o PIB a preços do ano "
        "anterior; não deve ser confundido com o IPCA (indicador separado, `ipca`), que mede "
        "apenas a inflação ao consumidor."
    ),
)
PIB_DEFLATOR_QUERY = SidraQuery(table=6784, variable=9811, classifications={})

CRESCIMENTO_PIB_AGROPECUARIO = StaticIndicatorMeta(
    slug="crescimento-pib-agropecuario",
    name="Crescimento do PIB agropecuário",
    category=IndicatorCategory.ECONOMIA,
    unit="%",
    polarity=IndicatorPolarity.higher_is_better,
    description_what=(
        "Variação trimestral do valor adicionado pela agropecuária ao PIB, em relação ao "
        "mesmo trimestre do ano anterior, já descontada a inflação."
    ),
    description_how=(
        "É fortemente influenciado pela safra agrícola do período — anos de safra recorde "
        "(como 2025) podem produzir altas de dois dígitos sem relação com política econômica "
        "de curto prazo. Compare sempre com os demais setores antes de atribuir a variação a "
        "um governo específico."
    ),
    update_frequency="trimestral",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Crescimento do PIB agropecuário\n\n"
        "Fonte: IBGE, Contas Nacionais Trimestrais — tabela SIDRA 5932, variável 6561 (\"Taxa "
        "trimestral, em relação ao mesmo período do ano anterior\"), classificação 11255 "
        "(\"Setores e subsetores\"), categoria 90687 (\"Agropecuária - total\").\n\n"
        "Cada ponto é datado no primeiro mês do trimestre a que se refere (jan/abr/jul/out)."
    ),
)
CRESCIMENTO_PIB_AGROPECUARIO_QUERY = SidraQuery(table=5932, variable=6561, classifications={11255: 90687})

CRESCIMENTO_PIB_INDUSTRIAL = StaticIndicatorMeta(
    slug="crescimento-pib-industrial",
    name="Crescimento do PIB industrial",
    category=IndicatorCategory.ECONOMIA,
    unit="%",
    polarity=IndicatorPolarity.higher_is_better,
    description_what=(
        "Variação trimestral do valor adicionado pela indústria ao PIB (extrativa, "
        "transformação, construção e eletricidade/água/saneamento), em relação ao mesmo "
        "trimestre do ano anterior, já descontada a inflação."
    ),
    description_how=(
        "Reflete o desempenho conjunto de fábricas, mineração, construção civil e utilidades. "
        "Um trimestre fraco pode refletir tanto queda de demanda interna quanto fatores "
        "externos (preço de commodities, juros para investimento)."
    ),
    update_frequency="trimestral",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Crescimento do PIB industrial\n\n"
        "Fonte: IBGE, Contas Nacionais Trimestrais — tabela SIDRA 5932, variável 6561, "
        "classificação 11255, categoria 90691 (\"Indústria - total\").\n\n"
        "Cada ponto é datado no primeiro mês do trimestre a que se refere (jan/abr/jul/out)."
    ),
)
CRESCIMENTO_PIB_INDUSTRIAL_QUERY = SidraQuery(table=5932, variable=6561, classifications={11255: 90691})

CRESCIMENTO_PIB_SERVICOS = StaticIndicatorMeta(
    slug="crescimento-pib-servicos",
    name="Crescimento do PIB de serviços",
    category=IndicatorCategory.ECONOMIA,
    unit="%",
    polarity=IndicatorPolarity.higher_is_better,
    description_what=(
        "Variação trimestral do valor adicionado pelo setor de serviços ao PIB (comércio, "
        "transporte, informação, atividades financeiras e imobiliárias, entre outros), em "
        "relação ao mesmo trimestre do ano anterior, já descontada a inflação."
    ),
    description_how=(
        "É o maior setor da economia brasileira em participação no PIB — costuma ser o mais "
        "estável dos três (agropecuária, indústria, serviços), refletindo consumo das famílias "
        "no dia a dia."
    ),
    update_frequency="trimestral",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Crescimento do PIB de serviços\n\n"
        "Fonte: IBGE, Contas Nacionais Trimestrais — tabela SIDRA 5932, variável 6561, "
        "classificação 11255, categoria 90696 (\"Serviços - total\").\n\n"
        "Cada ponto é datado no primeiro mês do trimestre a que se refere (jan/abr/jul/out)."
    ),
)
CRESCIMENTO_PIB_SERVICOS_QUERY = SidraQuery(table=5932, variable=6561, classifications={11255: 90696})

CRESCIMENTO_PIB_ADMINISTRACAO_PUBLICA = StaticIndicatorMeta(
    slug="crescimento-pib-administracao-publica",
    name="Crescimento do PIB de administração pública",
    category=IndicatorCategory.ECONOMIA,
    unit="%",
    polarity=IndicatorPolarity.neutral,
    description_what=(
        "Variação trimestral do valor adicionado por administração, saúde e educação públicas "
        "e seguridade social ao PIB, em relação ao mesmo trimestre do ano anterior, já "
        "descontada a inflação."
    ),
    description_how=(
        "Não é classificado como melhora/piora — mede principalmente o volume de gastos e "
        "serviços do setor público (folha de servidores, saúde e educação públicas), que pode "
        "crescer tanto por expansão deliberada de serviços quanto por outros fatores "
        "metodológicos, sem relação direta com qualidade de vida."
    ),
    update_frequency="trimestral",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Crescimento do PIB de administração pública\n\n"
        "Fonte: IBGE, Contas Nacionais Trimestrais — tabela SIDRA 5932, variável 6561, "
        "classificação 11255, categoria 90703 (\"Administração, saúde e educação públicas e "
        "seguridade social\").\n\n"
        "Cada ponto é datado no primeiro mês do trimestre a que se refere (jan/abr/jul/out)."
    ),
)
CRESCIMENTO_PIB_ADMINISTRACAO_PUBLICA_QUERY = SidraQuery(
    table=5932, variable=6561, classifications={11255: 90703}
)

TAXA_INVESTIMENTO = StaticIndicatorMeta(
    slug="taxa-investimento",
    name="Taxa de investimento",
    category=IndicatorCategory.ECONOMIA,
    unit="% do PIB",
    polarity=IndicatorPolarity.higher_is_better,
    description_what=(
        "Percentual do PIB que foi destinado à formação bruta de capital fixo (construção, "
        "máquinas, equipamentos) no trimestre, em vez de consumo imediato."
    ),
    description_how=(
        "Quanto maior, maior a parcela da economia voltada para ampliar a capacidade produtiva "
        "futura do país (estradas, fábricas, equipamentos), em vez de consumo corrente."
    ),
    update_frequency="trimestral",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Taxa de investimento\n\n"
        "Fonte: IBGE, Contas Nacionais Trimestrais — tabela SIDRA 6727, variável 2517. "
        "Cada ponto é datado no primeiro mês do trimestre a que se refere (jan/abr/jul/out)."
    ),
)
TAXA_INVESTIMENTO_QUERY = SidraQuery(table=6727, variable=2517, classifications={})

TAXA_POUPANCA = StaticIndicatorMeta(
    slug="taxa-poupanca",
    name="Taxa de poupança",
    category=IndicatorCategory.ECONOMIA,
    unit="% do PIB",
    polarity=IndicatorPolarity.neutral,
    description_what=(
        "Percentual do PIB que corresponde à poupança bruta da economia (renda não consumida) "
        "no trimestre — o principal financiador interno do investimento."
    ),
    description_how=(
        "Não é classificado como melhora/piora — uma taxa de poupança alta pode refletir tanto "
        "solidez financeira quanto retração do consumo das famílias; compare sempre com a taxa "
        "de investimento do mesmo período."
    ),
    update_frequency="trimestral",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Taxa de poupança\n\n"
        "Fonte: IBGE, Contas Nacionais Trimestrais — tabela SIDRA 6726, variável 9774. "
        "Cada ponto é datado no primeiro mês do trimestre a que se refere (jan/abr/jul/out)."
    ),
)
TAXA_POUPANCA_QUERY = SidraQuery(table=6726, variable=9774, classifications={})

TAXA_DESOCUPACAO_ANUAL = StaticIndicatorMeta(
    slug="taxa-desocupacao-anual",
    name="Taxa de desocupação (média anual)",
    category=IndicatorCategory.EMPREGO_RENDA,
    unit="%",
    polarity=IndicatorPolarity.lower_is_better,
    description_what=(
        "Percentual médio no ano de pessoas de 14 anos ou mais que estavam desocupadas (sem "
        "trabalho, mas disponíveis e procurando), em relação à força de trabalho, segundo a "
        "PNAD Contínua."
    ),
    description_how=(
        "Quanto menor, maior a proporção da força de trabalho que está ocupada. É a média das "
        "quatro estimativas trimestrais do ano — diferente do indicador `desemprego` (mensal, "
        "só Brasil), este tem quebra por estado."
    ),
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Taxa de desocupação (média anual)\n\n"
        "Fonte: IBGE, PNAD Contínua anual — tabela SIDRA 4562, variável 4099. Diferente do "
        "indicador `desemprego` (série mensal do SGS/BCB, só nível Brasil), esta versão é a "
        "média anual e está disponível por estado."
    ),
)
TAXA_DESOCUPACAO_ANUAL_QUERY = SidraQuery(table=4562, variable=4099, classifications={})

NIVEL_OCUPACAO = StaticIndicatorMeta(
    slug="nivel-ocupacao",
    name="Nível da ocupação",
    category=IndicatorCategory.EMPREGO_RENDA,
    unit="%",
    polarity=IndicatorPolarity.higher_is_better,
    description_what=(
        "Percentual médio no ano de pessoas de 14 anos ou mais que estavam ocupadas (com "
        "trabalho) em relação ao total de pessoas em idade de trabalhar, segundo a PNAD "
        "Contínua."
    ),
    description_how=(
        "Diferente da taxa de desocupação (que só considera quem está procurando emprego), o "
        "nível de ocupação usa como base todas as pessoas em idade de trabalhar — inclui "
        "quem desistiu de procurar emprego. Quanto maior, maior a proporção da população "
        "efetivamente trabalhando."
    ),
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Nível da ocupação\n\n"
        "Fonte: IBGE, PNAD Contínua anual — tabela SIDRA 4363, variável 4097."
    ),
)
NIVEL_OCUPACAO_QUERY = SidraQuery(table=4363, variable=4097, classifications={})

RENDIMENTO_MEDIO_ANUAL = StaticIndicatorMeta(
    slug="rendimento-medio-anual",
    name="Rendimento médio mensal real (média anual)",
    category=IndicatorCategory.EMPREGO_RENDA,
    unit="R$",
    polarity=IndicatorPolarity.higher_is_better,
    description_what=(
        "Rendimento médio mensal real (já descontada a inflação) que as pessoas ocupadas "
        "recebem habitualmente em todos os trabalhos, média do ano, segundo a PNAD Contínua."
    ),
    description_how=(
        "Como é uma média, é sensível à composição da força de trabalho no período — compare "
        "sempre com a taxa de desocupação e o nível de ocupação do mesmo ano. Diferente do "
        "indicador `rendimento-medio-real` (mensal, só Brasil), este é a média anual e está "
        "disponível por estado."
    ),
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Rendimento médio mensal real (média anual)\n\n"
        "Fonte: IBGE, PNAD Contínua anual — tabela SIDRA 4660, variável 5933 (\"Rendimento "
        "médio mensal real... habitualmente recebido em todos os trabalhos\")."
    ),
)
RENDIMENTO_MEDIO_ANUAL_QUERY = SidraQuery(table=4660, variable=5933, classifications={})

TAXA_INFORMALIDADE = StaticIndicatorMeta(
    slug="taxa-informalidade",
    name="Taxa de informalidade",
    category=IndicatorCategory.EMPREGO_RENDA,
    unit="%",
    polarity=IndicatorPolarity.lower_is_better,
    description_what=(
        "Percentual médio no ano de pessoas ocupadas de 14 anos ou mais que trabalhavam sem "
        "carteira assinada, sem CNPJ próprio regularizado ou fora de outras formas de "
        "contribuição previdenciária formal, segundo a PNAD Contínua."
    ),
    description_how=(
        "Quanto maior, maior a proporção de trabalhadores sem os direitos e proteções "
        "associados ao trabalho formal (férias, FGTS, previdência). Não deve ser confundido "
        "com desemprego — um informal está ocupado, só não tem vínculo formal."
    ),
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Taxa de informalidade\n\n"
        "Fonte: IBGE, PNAD Contínua anual — tabela SIDRA 4708, variável 12466."
    ),
)
TAXA_INFORMALIDADE_QUERY = SidraQuery(table=4708, variable=12466, classifications={})

INDICE_GINI_RENDA = StaticIndicatorMeta(
    slug="indice-gini-renda",
    name="Índice de Gini da renda domiciliar per capita",
    category=IndicatorCategory.EMPREGO_RENDA,
    unit="índice (0 a 1)",
    polarity=IndicatorPolarity.lower_is_better,
    description_what=(
        "Medida de desigualdade na distribuição da renda domiciliar per capita — varia de 0 "
        "(todos os domicílios têm a mesma renda por pessoa) a 1 (uma única pessoa concentra "
        "toda a renda)."
    ),
    description_how=(
        "Quanto menor, mais igualitária é a distribuição de renda entre os domicílios. O "
        "Brasil está historicamente entre os países mais desiguais do mundo nesse índice, "
        "ainda que com queda observada nos últimos anos."
    ),
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Índice de Gini da renda domiciliar per capita\n\n"
        "Fonte: IBGE, PNAD Contínua anual — tabela SIDRA 7435, variável 10681 (\"Índice de "
        "Gini do rendimento domiciliar per capita, a preços médios do ano\")."
    ),
)
INDICE_GINI_RENDA_QUERY = SidraQuery(table=7435, variable=10681, classifications={})
