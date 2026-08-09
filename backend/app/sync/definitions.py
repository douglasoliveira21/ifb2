"""Especificação dos indicadores integrados na Fase 2.

Cada spec descreve tudo que o sync precisa: de onde buscar o dado (série
SGS do BCB), como normalizá-lo, e os metadados que alimentam
`indicator_definitions` / `indicator_methodologies` / `sources`.
"""
from dataclasses import dataclass

from app.models.indicator_definition import IndicatorCategory, IndicatorPolarity


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
