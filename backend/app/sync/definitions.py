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

TAXA_POBREZA = StaticIndicatorMeta(
    slug="taxa-pobreza",
    name="Taxa de pobreza",
    category=IndicatorCategory.POBREZA,
    unit="%",
    polarity=IndicatorPolarity.lower_is_better,
    description_what=(
        "Percentual da população vivendo em domicílios com rendimento domiciliar per capita "
        "abaixo da linha de pobreza nacional (indicador 1.2.1 dos Objetivos de Desenvolvimento "
        "Sustentável da ONU, com linha de corte definida pelo IBGE para o Brasil)."
    ),
    description_how=(
        "Quanto menor, melhor. Diferente da taxa de extrema pobreza (linha de corte mais "
        "baixa, padrão internacional do Banco Mundial), esta usa uma linha de pobreza mais "
        "alta, definida nacionalmente — por isso o percentual é maior."
    ),
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Taxa de pobreza\n\n"
        "Fonte: IBGE, PNAD Contínua — tabela SIDRA 5877, variável 9948 (\"Proporção da "
        "população abaixo da linha de pobreza nacional\"), indicador 1.2.1 dos Objetivos de "
        "Desenvolvimento Sustentável (ODS) da ONU.\n\n"
        "A linha de pobreza nacional é definida pelo IBGE especificamente para o Brasil — "
        "diferente da linha de extrema pobreza (indicador ODS 1.1.1, ver `taxa-extrema-"
        "pobreza`), que usa um padrão internacional do Banco Mundial. As duas medem coisas "
        "diferentes e não devem ser somadas.\n\n"
        "Conferido: Brasil 2024 = 26,5% — consistente com a queda de pobreza amplamente "
        "noticiada entre 2022 e 2024."
    ),
)
TAXA_POBREZA_QUERY = SidraQuery(table=5877, variable=9948)

TAXA_EXTREMA_POBREZA = StaticIndicatorMeta(
    slug="taxa-extrema-pobreza",
    name="Taxa de extrema pobreza",
    category=IndicatorCategory.POBREZA,
    unit="%",
    polarity=IndicatorPolarity.lower_is_better,
    description_what=(
        "Percentual da população vivendo em domicílios com rendimento domiciliar per capita "
        "abaixo da linha internacional de extrema pobreza do Banco Mundial (US$ 2,15 por dia, "
        "PPC — indicador 1.1.1 dos Objetivos de Desenvolvimento Sustentável da ONU)."
    ),
    description_how=(
        "Quanto menor, melhor. Usa uma linha de corte mais baixa que a taxa de pobreza "
        "nacional (`taxa-pobreza`), por isso o percentual é menor — mede a parcela da "
        "população em situação de privação mais severa."
    ),
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Taxa de extrema pobreza\n\n"
        "Fonte: IBGE, PNAD Contínua — tabela SIDRA 5817, variável 9617 (\"Proporção da "
        "população abaixo da linha de pobreza internacional\"), indicador 1.1.1 dos Objetivos "
        "de Desenvolvimento Sustentável (ODS) da ONU — linha de extrema pobreza do Banco "
        "Mundial (US$ 2,15/dia, paridade de poder de compra).\n\n"
        "Conferido: Brasil 2024 = 4,7% — na mesma ordem de grandeza da queda de extrema "
        "pobreza amplamente noticiada no período."
    ),
)
TAXA_EXTREMA_POBREZA_QUERY = SidraQuery(table=5817, variable=9617)

TAXA_INSEGURANCA_ALIMENTAR = StaticIndicatorMeta(
    slug="taxa-inseguranca-alimentar",
    name="Taxa de insegurança alimentar",
    category=IndicatorCategory.POBREZA,
    unit="%",
    polarity=IndicatorPolarity.lower_is_better,
    description_what=(
        "Percentual de domicílios particulares em que os moradores relataram algum grau de "
        "insegurança alimentar (leve, moderada ou grave) — ou seja, incerteza ou restrição no "
        "acesso a alimentos por falta de recursos, mesmo que não cheguem a passar fome."
    ),
    description_how=(
        "Quanto menor, melhor. Soma os três graus de insegurança alimentar (leve, moderada e "
        "grave) medidos pela Escala Brasileira de Insegurança Alimentar (EBIA) — não distingue "
        "aqui entre \"preocupação em faltar comida\" (leve) e privação severa (grave)."
    ),
    update_frequency="irregular — levantamento não é anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Taxa de insegurança alimentar\n\n"
        "Fonte: IBGE, PNAD Contínua (suplemento de Segurança Alimentar) — tabela SIDRA 6665, "
        "indicador 2.1.2 dos Objetivos de Desenvolvimento Sustentável (ODS), variável 800 "
        "(\"Domicílios particulares\", % ), categoria \"Com insegurança alimentar\" (soma dos "
        "graus leve, moderada e grave) da classificação \"Situação de segurança alimentar\".\n\n"
        "**Só nível Brasil**: esta tabela do SIDRA só publica o resultado nacional, sem quebra "
        "por estado.\n\n"
        "**Levantamento não é anual**: o suplemento de segurança alimentar da PNAD Contínua só "
        "roda em anos específicos (2004, 2009, 2013, 2018, 2023, 2024 até agora) — a série "
        "aparece com lacunas nos anos em que a pesquisa não foi a campo, isso é do "
        "levantamento, não uma falha de sincronização.\n\n"
        "Conferido: Brasil 2024 = 24,2% dos domicílios, seguindo a tendência de queda já "
        "documentada desde o pico da pandemia."
    ),
)
TAXA_INSEGURANCA_ALIMENTAR_QUERY = SidraQuery(table=6665, variable=800, classifications={12404: 109099})

RAZAO_DESIGUALDADE_RACIAL_RENDA = StaticIndicatorMeta(
    slug="razao-desigualdade-racial-renda",
    name="Desigualdade racial de renda",
    category=IndicatorCategory.POBREZA,
    unit="% da taxa de pessoas brancas",
    polarity=IndicatorPolarity.lower_is_better,
    description_what=(
        "Percentual de pessoas pretas vivendo com renda domiciliar per capita abaixo de 50% "
        "da renda mediana nacional, como proporção do mesmo percentual entre pessoas brancas. "
        "Acima de 100% significa que pessoas pretas têm mais chance de estar nessa faixa de "
        "renda baixa do que pessoas brancas."
    ),
    description_how=(
        "Quanto mais perto de 100%, menor a disparidade racial. Compara só as categorias "
        "\"preta\" e \"branca\" da classificação oficial de cor/raça do IBGE — não inclui "
        "parda, amarela ou indígena nesta razão, embora o IBGE publique dados também para "
        "essas categorias."
    ),
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Desigualdade racial de renda\n\n"
        "Fonte: IBGE, PNAD Contínua — tabela SIDRA 6583, indicador 10.2.1 dos Objetivos de "
        "Desenvolvimento Sustentável (ODS), variável 4971 (\"Percentual de pessoas vivendo com "
        "abaixo de 50% do rendimento mediano mensal real domiciliar per capita\"), "
        "classificação \"Cor ou raça\", categorias \"Preta\" e \"Branca\".\n\n"
        "O IFB busca as duas séries separadamente e calcula a razão preta/branca em cada ano "
        "— a própria tabela do SIDRA não traz essa razão pronta (mesmo método já usado para a "
        "razão de rendimento mulher/homem). Só nível Brasil — a tabela não tem quebra por "
        "estado.\n\n"
        "Conferido: Brasil 2024 — 24,0% das pessoas pretas vs. 13,8% das pessoas brancas "
        "vivem abaixo dessa linha de renda, uma razão de ~174%, consistente com a desigualdade "
        "racial de renda amplamente documentada pelo próprio IBGE."
    ),
)
RENDA_ABAIXO_MEDIANA_PRETA_QUERY = SidraQuery(table=6583, variable=4971, classifications={86: 2777})
RENDA_ABAIXO_MEDIANA_BRANCA_QUERY = SidraQuery(table=6583, variable=4971, classifications={86: 2776})

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

TAXA_ABANDONO_ENSINO_MEDIO = StaticIndicatorMeta(
    slug="taxa-abandono-ensino-medio",
    name="Taxa de abandono escolar (Ensino Médio)",
    category=IndicatorCategory.EDUCACAO,
    unit="%",
    polarity=IndicatorPolarity.lower_is_better,
    description_what=(
        "Percentual de matrículas do Ensino Médio que terminaram o ano letivo sem "
        "aprovação nem reprovação — o aluno simplesmente deixou de frequentar a escola "
        "antes do fim do ano, segundo o Censo Escolar."
    ),
    description_how=(
        "Quanto menor, melhor. Considera todas as redes (federal, estadual, municipal e "
        "privada) e localizações (urbana e rural) combinadas."
    ),
    update_frequency="anual",
    source=SOURCE_INEP,
    methodology=(
        "# Metodologia — Taxa de abandono escolar (Ensino Médio)\n\n"
        "Fonte: INEP, Censo Escolar — planilha \"Taxas de Rendimento Escolar\" (Aprovação, "
        "Reprovação e Abandono), publicada anualmente em "
        "gov.br/inep/dados-abertos/indicadores-educacionais/taxas-de-rendimento. Leitura da "
        "coluna \"Taxa de Abandono — Ensino Médio — Total\" (código de coluna `3_CAT_MED`), "
        "filtrando Localização=\"Total\" e Dependência Administrativa=\"Total\" (todas as "
        "redes e áreas combinadas).\n\n"
        "**Sem série histórica automática**: diferente do IDEB (uma planilha só com todos os "
        "anos), esta fonte publica um arquivo novo por ano — a URL muda a cada edição. Por "
        "ora o IFB só sincroniza o ano mais recente (2025); os anos anteriores (2012–2024, "
        "cada um com arquivo próprio no mesmo padrão) ainda não foram integrados.\n\n"
        "Conferido: Brasil 2025 = 2,2%, São Paulo 2025 = 2,8% — valores consistentes com o "
        "abandono no Ensino Médio já documentado pelo INEP em anos recentes."
    ),
)

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

SOURCE_RIPSA_MORTALIDADE_MATERNA = SourceSpec(
    key="ripsa-mortalidade-materna",
    name="Ministério da Saúde — RIPSA (Rede Interagencial de Informação para a Saúde)",
    url="https://dadosabertos.saude.gov.br/dataset/ripsa-mortalidade-dimensao-2-mortalidade-materna",
    description=(
        "Indicador MRT.2.01 (Razão de Mortalidade Materna) do catálogo RIPSA, calculado a "
        "partir do Sistema de Informações sobre Mortalidade (SIM) e do Sistema de Informações "
        "sobre Nascidos Vivos (Sinasc), publicado no Portal de Dados Abertos do SUS."
    ),
)

SOURCE_RIPSA_MORTALIDADE_TRANSITO = SourceSpec(
    key="ripsa-mortalidade-transito",
    name="Ministério da Saúde — RIPSA (Rede Interagencial de Informação para a Saúde)",
    url="https://dadosabertos.saude.gov.br/dataset/ripsa-mortalidade-dimensao-4-mortalidade-por-causas-externas",
    description=(
        "Indicador MRT.4.03 (Taxa de Mortalidade por Lesão de Trânsito) do catálogo RIPSA, "
        "calculado a partir do Sistema de Informações sobre Mortalidade (SIM), publicado no "
        "Portal de Dados Abertos do SUS."
    ),
)

SOURCE_TESOURO_CARGA_TRIBUTARIA = SourceSpec(
    key="tesouro-carga-tributaria",
    name="Tesouro Nacional — Carga Tributária do Governo Geral",
    url="https://www.tesourotransparente.gov.br/publicacoes/carga-tributaria-do-governo-geral",
    description=(
        "Secretaria do Tesouro Nacional — boletim anual da Carga Tributária Bruta do Governo "
        "Geral, metodologia do Manual de Estatísticas de Finanças Públicas (MEFP/GFSM 2014, "
        "FMI)."
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

TAXA_FEMINICIDIO_ESTADUAL = StaticIndicatorMeta(
    slug="taxa-feminicidio-estadual",
    name="Taxa de feminicídio",
    category=IndicatorCategory.MULHERES,
    unit="por 100 mil mulheres",
    polarity=IndicatorPolarity.lower_is_better,
    description_what=(
        "Número de feminicídios (homicídio de mulher pela condição de sexo feminino, conforme "
        "tipificação do art. 121, §2º-A do Código Penal) por 100 mil mulheres — diferente da "
        "taxa geral de homicídios de mulheres, que inclui também mortes não motivadas pelo "
        "gênero da vítima."
    ),
    description_how=(
        "Quanto menor, melhor. É uma taxa (por 100 mil mulheres), não um número absoluto — "
        "permite comparar estados de tamanhos diferentes diretamente."
    ),
    update_frequency="anual",
    source=SOURCE_FBSP,
    methodology=(
        "# Metodologia — Taxa de feminicídio por estado\n\n"
        "Mesma fonte e mesmas ressalvas do indicador de Mortes Violentas Intencionais (MVI) — "
        "ver metodologia daquele indicador para o histórico de por que o IFB usa o FBSP em vez "
        "da fonte oficial (Sinesp/MJSP). Aqui a leitura vem da Tabela 24 do Anuário "
        "(\"Homicídios de mulheres e feminicídios\"), coluna \"Taxa\" da seção "
        "\"Feminicídios\" — não confundir com a coluna \"Taxa\" da seção \"Homicídios "
        "(incluindo feminicídios)\" da mesma tabela, que é a taxa geral de homicídio de "
        "mulheres (número maior, inclui feminicídios e outros homicídios de mulheres).\n\n"
        "Conferido contra o número nacional amplamente noticiado na divulgação da edição 2025: "
        "Brasil 2024 = 1,4 por 100 mil mulheres (recorde histórico da série do FBSP)."
    ),
)

LETALIDADE_POLICIAL_ESTADUAL = StaticIndicatorMeta(
    slug="letalidade-policial-estadual",
    name="Letalidade policial",
    category=IndicatorCategory.SEGURANCA,
    unit="por 100 mil habitantes",
    polarity=IndicatorPolarity.lower_is_better,
    description_what=(
        "Mortes decorrentes de intervenções de policiais civis e militares, em serviço e fora "
        "de serviço, por 100 mil habitantes."
    ),
    description_how=(
        "Quanto menor, melhor. Não distingue mortes consideradas legítimas (confronto armado) "
        "de excessos — mede o volume total de mortes em intervenções policiais, não a "
        "legalidade de cada caso."
    ),
    update_frequency="anual",
    source=SOURCE_FBSP,
    methodology=(
        "# Metodologia — Letalidade policial por estado\n\n"
        "Mesma fonte e mesmas ressalvas do indicador de Mortes Violentas Intencionais (MVI) — "
        "ver metodologia daquele indicador. Leitura da Tabela 09 do Anuário (\"Mortes "
        "decorrentes de intervenções policiais, segundo corporação e situação\"), coluna "
        "\"Taxa\" (soma de policiais civis e militares, em serviço e fora de serviço).\n\n"
        "Conferido contra a divulgação oficial: Brasil 2024 = 2,94 por 100 mil habitantes."
    ),
)

ROUBO_TOTAL_ESTADUAL = StaticIndicatorMeta(
    slug="roubo-total-estadual",
    name="Taxa de roubo (total)",
    category=IndicatorCategory.SEGURANCA,
    unit="por 100 mil habitantes",
    polarity=IndicatorPolarity.lower_is_better,
    description_what=(
        "Soma de todas as modalidades de roubo (a pessoa, veículo, residência, comércio, "
        "instituição financeira, carga etc.) registradas pelas polícias estaduais, por 100 mil "
        "habitantes."
    ),
    description_how=(
        "Quanto menor, melhor. Mede roubo (crime com ameaça ou violência), não furto (sem "
        "confronto com a vítima) — as duas categorias são registradas e contadas separadamente "
        "pelas polícias."
    ),
    update_frequency="anual",
    source=SOURCE_FBSP,
    methodology=(
        "# Metodologia — Taxa de roubo (total) por estado\n\n"
        "Mesma fonte e mesmas ressalvas do indicador de Mortes Violentas Intencionais (MVI) — "
        "ver metodologia daquele indicador. Leitura da Tabela 17 do Anuário (\"Roubo a "
        "instituição financeira, de carga e roubo total\"), coluna \"Taxa\" da seção \"Roubo "
        "(total)\" — não confundir com as colunas \"Taxa\" das seções específicas de roubo a "
        "instituição financeira ou roubo de carga, na mesma tabela.\n\n"
        "Conferido contra a divulgação oficial: Brasil 2024 = 350,6 por 100 mil habitantes."
    ),
)

CARGA_TRIBUTARIA_GOVERNO_GERAL = StaticIndicatorMeta(
    slug="carga-tributaria-governo-geral",
    name="Carga tributária bruta do governo geral (% do PIB)",
    category=IndicatorCategory.CONTAS_PUBLICAS,
    unit="%",
    polarity=IndicatorPolarity.neutral,
    description_what=(
        "Soma de todos os tributos arrecadados no Brasil — União, estados e municípios — "
        "dividida pelo PIB do ano. Mede o peso total da arrecadação tributária na economia, "
        "não a eficiência ou a justiça de como esse dinheiro é cobrado ou gasto."
    ),
    description_how=(
        "Indicador neutro: carga tributária alta ou baixa não é, por si só, bom ou ruim — "
        "depende do que o Estado entrega em troca (serviços públicos, investimento) e de como "
        "a cobrança é distribuída entre a população. O IFB não classifica este indicador como "
        "\"melhorou\"/\"piorou\"."
    ),
    update_frequency="anual",
    source=SOURCE_TESOURO_CARGA_TRIBUTARIA,
    methodology=(
        "# Metodologia — Carga tributária bruta do governo geral\n\n"
        "Fonte: Secretaria do Tesouro Nacional, boletim \"Carga Tributária do Governo "
        "Geral\", anexo \"Base CTB GG.xlsx\", Tabela 1, linha \"Governo Geral\" do bloco em "
        "% do PIB (soma União + estados + municípios). Metodologia do Manual de Estatísticas "
        "de Finanças Públicas (MEFP/GFSM 2014) do FMI.\n\n"
        "**Só nível Brasil**: a carga tributária bruta soma a arrecadação de todas as esferas "
        "de governo sobre o PIB nacional — não é um dado declarado por ente federativo como o "
        "SICONFI, então não existe quebra por estado ou município.\n\n"
        "**Sem série histórica automática**: o Tesouro publica um anexo novo a cada edição — a "
        "URL do arquivo muda a cada divulgação e precisa ser atualizada manualmente no código "
        "(mesmo padrão já usado para o IDEB/INEP e o Anuário/FBSP). A edição vigente (2025) "
        "traz a série completa desde 2010.\n\n"
        "Conferido contra a divulgação oficial: Brasil 2025 = 32,40% do PIB (maior valor da "
        "série histórica, +0,18 ponto percentual sobre 2024 = 32,22%)."
    ),
)

RAZAO_MORTALIDADE_MATERNA_ESTADUAL = StaticIndicatorMeta(
    slug="razao-mortalidade-materna-estadual",
    name="Razão de mortalidade materna",
    category=IndicatorCategory.SAUDE,
    unit="por 100 mil nascidos vivos",
    polarity=IndicatorPolarity.lower_is_better,
    description_what=(
        "Número de óbitos de mulheres por causas relacionadas à gravidez, parto ou puerpério "
        "(até 42 dias após o fim da gestação), por 100 mil nascidos vivos — um dos indicadores "
        "de saúde pública mais usados internacionalmente para medir a qualidade da assistência "
        "à gestação e ao parto."
    ),
    description_how=(
        "Quanto menor, melhor. O número de óbitos maternos é pequeno e varia bastante de ano "
        "para ano em estados menores — por isso o Ministério da Saúde aplica um \"fator de "
        "correção\" aos óbitos declarados, para compensar a subnotificação já documentada no "
        "sistema de registro civil."
    ),
    update_frequency="anual",
    source=SOURCE_RIPSA_MORTALIDADE_MATERNA,
    methodology=(
        "# Metodologia — Razão de mortalidade materna por estado\n\n"
        "Fonte: indicador MRT.2.01 do catálogo RIPSA (Rede Interagencial de Informação para a "
        "Saúde), calculado pelo Ministério da Saúde a partir do cruzamento entre o Sistema de "
        "Informações sobre Mortalidade (SIM) e o Sistema de Informações sobre Nascidos Vivos "
        "(Sinasc), publicado como CSV no Portal de Dados Abertos do SUS.\n\n"
        "O arquivo traz numerador (óbitos maternos já com fator de correção de subnotificação "
        "aplicado pelo Ministério) e denominador (nascidos vivos) separados, não a razão "
        "pronta — o IFB calcula `(óbitos corrigidos ÷ nascidos vivos) × 100.000` para cada "
        "estado e ano. Para o valor nacional, o IFB soma o numerador e o denominador de todos "
        "os 27 estados antes de calcular a razão (agregação correta para uma taxa — a média "
        "simples das 27 razões estaduais distorceria o resultado a favor de estados com poucos "
        "nascimentos).\n\n"
        "**Defasagem de publicação**: dado de mortalidade tem atraso de consolidação — a série "
        "disponível vai até 2023 (não o ano corrente), reflexo do tempo que os sistemas SIM/"
        "Sinasc levam para fechar um ano de registros de forma confiável.\n\n"
        "Conferido contra fato amplamente documentado: o valor nacional salta para 117,4 por "
        "100 mil nascidos vivos em 2021 — o pico da pandemia de covid-19, quando complicações "
        "da doença em gestantes elevaram a mortalidade materna no Brasil, revertendo em 2022-"
        "2023 para patamar próximo ao pré-pandemia (~55-58)."
    ),
)

TAXA_MORTALIDADE_TRANSITO_ESTADUAL = StaticIndicatorMeta(
    slug="taxa-mortalidade-transito-estadual",
    name="Taxa de mortalidade por lesão de trânsito",
    category=IndicatorCategory.SAUDE,
    unit="por 100 mil habitantes",
    polarity=IndicatorPolarity.lower_is_better,
    description_what=(
        "Número de óbitos causados por acidentes de trânsito (pedestres, ciclistas, "
        "motociclistas, ocupantes de automóveis e outros veículos), por 100 mil habitantes."
    ),
    description_how=(
        "Quanto menor, melhor. Soma todos os tipos de vítima de trânsito (não separa "
        "pedestre, motociclista etc.), então não distingue causas específicas — infraestrutura "
        "viária, fiscalização, frota de motos, entre outros fatores, todos afetam este número "
        "de formas diferentes."
    ),
    update_frequency="anual",
    source=SOURCE_RIPSA_MORTALIDADE_TRANSITO,
    methodology=(
        "# Metodologia — Taxa de mortalidade por lesão de trânsito por estado\n\n"
        "Fonte: indicador MRT.4.03 do catálogo RIPSA (Rede Interagencial de Informação para a "
        "Saúde), calculado pelo Ministério da Saúde a partir do Sistema de Informações sobre "
        "Mortalidade (SIM), publicado como CSV no Portal de Dados Abertos do SUS.\n\n"
        "O arquivo de origem traz uma linha por combinação de UF, município, ano, sexo e "
        "faixa etária (~1,7 milhão de linhas, 2000–2024) — o IFB soma o numerador (óbitos) e "
        "o denominador (população estimada) de todas as linhas de um mesmo estado e ano antes "
        "de calcular a taxa (agregação correta — soma antes de dividir, não a média das taxas "
        "municipais).\n\n"
        "Conferido: Brasil 2024 = 17,48 por 100 mil habitantes, na mesma ordem de grandeza das "
        "cerca de 37 mil mortes no trânsito por ano já amplamente noticiadas para o Brasil."
    ),
)

SOURCE_SISDEPEN = SourceSpec(
    key="sisdepen",
    name="Secretaria Nacional de Políticas Penais (Senappen) — SISDEPEN",
    url="https://www.gov.br/senappen/pt-br/servicos/sisdepen/bases-de-dados",
    description=(
        "Levantamento Nacional de Informações Penitenciárias (SISDEPEN), censo semestral de "
        "todas as unidades prisionais brasileiras conduzido pela Secretaria Nacional de "
        "Políticas Penais (Ministério da Justiça e Segurança Pública)."
    ),
)

TAXA_OCUPACAO_PRISIONAL_ESTADUAL = StaticIndicatorMeta(
    slug="taxa-ocupacao-prisional-estadual",
    name="Taxa de ocupação do sistema prisional",
    category=IndicatorCategory.SEGURANCA,
    unit="% da capacidade",
    polarity=IndicatorPolarity.lower_is_better,
    description_what=(
        "Proporção entre o número de pessoas presas e o número de vagas declaradas pelos "
        "próprios estabelecimentos penais. Acima de 100% significa que o sistema abriga mais "
        "presos do que sua capacidade projetada — superlotação."
    ),
    description_how=(
        "Quanto menor, melhor (mais perto de 100% = sistema dentro da capacidade projetada). "
        "A capacidade é autodeclarada por cada unidade prisional no censo, não é uma medida "
        "externa auditada — varia conforme o critério de cada gestão estadual sobre o que "
        "conta como vaga disponível."
    ),
    update_frequency="semestral",
    source=SOURCE_SISDEPEN,
    methodology=(
        "# Metodologia — Taxa de ocupação do sistema prisional por estado\n\n"
        "Fonte: Levantamento Nacional de Informações Penitenciárias (SISDEPEN/Senappen), CSV "
        "censitário com uma linha por unidade prisional (~1.700 colunas, ciclo semestral).\n\n"
        "O IFB soma, por estado, a capacidade declarada (colunas '1.3 Capacidade do "
        "estabelecimento | Masculino | Total' + '...Feminino | Total') e a população prisional "
        "total (coluna '5.1 Quantidade de pessoas privadas de liberdade por faixa etária | "
        "Total') de todas as unidades daquele estado, e calcula população/capacidade × 100 "
        "(agregação correta — soma antes de dividir).\n\n"
        "**Sem série histórica em arquivo único**: cada ciclo semestral é publicado como um "
        "CSV separado, sem um consolidado histórico para download direto — o indicador reflete "
        "só o ciclo mais recente disponível, e a URL de origem precisa ser atualizada a cada "
        "novo ciclo (mesma limitação já documentada para as Taxas de Rendimento do INEP).\n\n"
        "Conferido: 19º ciclo (2º semestre de 2025) — Brasil: 679.763 vagas declaradas, "
        "936.981 pessoas presas, taxa de ocupação 137,8%, mesma ordem de grandeza da "
        "superlotação já amplamente noticiada para o sistema prisional brasileiro."
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

OBITOS_CAUSAS_NAO_NATURAIS = StaticIndicatorMeta(
    slug="obitos-causas-nao-naturais",
    name="Óbitos por causas não naturais",
    category=IndicatorCategory.SAUDE,
    unit="óbitos",
    polarity=IndicatorPolarity.lower_is_better,
    description_what=(
        "Número de óbitos registrados no ano cuja causa foi classificada como 'não natural' "
        "no registro civil — inclui acidentes (de trânsito, de trabalho, entre outros), "
        "suicídios e homicídios, mas não abre o total por tipo de causa."
    ),
    description_how=(
        "É uma contagem absoluta (não uma taxa), então cresce naturalmente com a população — "
        "compare sempre proporcionalmente ao tamanho do estado antes de comparar estados "
        "diferentes. Não deve ser confundido com a Taxa de Mortes Violentas Intencionais "
        "(indicador `taxa-mortes-violentas-intencionais-estadual`), que é mais específica "
        "(só homicídios/latrocínios/lesão corporal seguida de morte) e vem de uma fonte "
        "diferente (Fórum Brasileiro de Segurança Pública, não-governamental)."
    ),
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Óbitos por causas não naturais\n\n"
        "Fonte: IBGE, Estatísticas do Registro Civil — tabela SIDRA 2681, variável 343, "
        "classificação 1836 (\"Natureza do óbito\"), categoria 99818 (\"Não natural\"). Conta "
        "óbitos registrados no ano cuja causa básica foi classificada como não natural pelo "
        "cartório de registro civil, a partir da declaração de óbito.\n\n"
        "É um número diferente do que apuram sistemas de vigilância epidemiológica como o SIM "
        "(Sistema de Informação sobre Mortalidade) do Ministério da Saúde — o Registro Civil "
        "conta o evento registrado em cartório, sem detalhar o tipo específico de causa "
        "não natural (acidente, suicídio, homicídio etc. aparecem juntos nesta categoria)."
    ),
)
OBITOS_CAUSAS_NAO_NATURAIS_QUERY = SidraQuery(
    table=2681, variable=343, classifications={1836: 99818, 244: 0, 2: 0, 260: 0, 257: 0}
)

MEDIA_ANOS_ESTUDO = StaticIndicatorMeta(
    slug="media-anos-estudo",
    name="Número médio de anos de estudo",
    category=IndicatorCategory.EDUCACAO,
    unit="anos",
    polarity=IndicatorPolarity.higher_is_better,
    description_what=(
        "Número médio de anos de estudo completos das pessoas de 15 anos ou mais de idade, "
        "segundo a PNAD Contínua."
    ),
    description_how=(
        "Quanto maior, mais anos de escolaridade completa a população adulta acumulou em "
        "média. É um indicador de estoque (reflete décadas de política educacional "
        "acumulada), então muda pouco de um ano para o outro — mudanças relevantes aparecem "
        "em janelas de vários anos, não de um mandato isolado."
    ),
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Número médio de anos de estudo\n\n"
        "Fonte: IBGE, PNAD Contínua anual — tabela SIDRA 7126, variável 3593, classificações "
        "2 (\"Sexo\"), categoria 6794 (\"Total\") e 58 (\"Grupo de idade\"), categoria 2795 "
        "(\"15 anos ou mais\")."
    ),
)
MEDIA_ANOS_ESTUDO_QUERY = SidraQuery(table=7126, variable=3593, classifications={2: 6794, 58: 2795})

ESCOLARIDADE_AVANCADA = StaticIndicatorMeta(
    slug="escolaridade-avancada",
    name="Pessoas com 12 anos ou mais de estudo (25 anos ou mais)",
    category=IndicatorCategory.EDUCACAO,
    unit="%",
    polarity=IndicatorPolarity.higher_is_better,
    description_what=(
        "Percentual de pessoas de 25 anos ou mais de idade que completaram 12 anos ou mais "
        "de estudo — aproximadamente equivalente a ter concluído o ensino médio ou mais, "
        "segundo a PNAD Contínua."
    ),
    description_how=(
        "Quanto maior, maior a proporção da população adulta com pelo menos ensino médio "
        "completo. Assim como o número médio de anos de estudo, é um indicador de estoque "
        "educacional acumulado — muda lentamente, ano a ano."
    ),
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Pessoas com 12 anos ou mais de estudo (25 anos ou mais)\n\n"
        "Fonte: IBGE, PNAD Contínua anual — tabela SIDRA 7133, variável 10270 (\"Distribuição "
        "percentual das pessoas de 25 anos ou mais de idade\"), classificações 2 (\"Sexo\"), "
        "categoria 6794 (\"Total\") e 71 (\"Grupos de anos de estudo\"), categoria 6664 "
        "(\"12 anos ou mais\")."
    ),
)
ESCOLARIDADE_AVANCADA_QUERY = SidraQuery(table=7133, variable=10270, classifications={2: 6794, 71: 6664})

DOMICILIOS_ALUGADOS = StaticIndicatorMeta(
    slug="domicilios-alugados",
    name="Domicílios alugados",
    category=IndicatorCategory.HABITACAO,
    unit="%",
    polarity=IndicatorPolarity.neutral,
    description_what=(
        "Percentual de domicílios particulares permanentes que estavam alugados, segundo a "
        "PNAD Contínua."
    ),
    description_how=(
        "Não é classificado como melhora/piora — um aumento pode refletir tanto maior acesso "
        "ao mercado de aluguel quanto dificuldade crescente de comprar a casa própria, "
        "dependendo do contexto de preços de imóveis e crédito habitacional do período."
    ),
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Domicílios alugados\n\n"
        "Fonte: IBGE, PNAD Contínua anual — tabela SIDRA 6821, variável 9784 (\"Distribuição "
        "percentual dos domicílios\"), classificação 63 (\"Condição de ocupação do "
        "domicílio\"), categoria 1055 (\"Alugado\")."
    ),
)
DOMICILIOS_ALUGADOS_QUERY = SidraQuery(table=6821, variable=9784, classifications={63: 1055})

DOMICILIOS_SEM_DOCUMENTO_PROPRIEDADE = StaticIndicatorMeta(
    slug="domicilios-sem-documento-propriedade",
    name="Domicílios próprios sem documento de propriedade",
    category=IndicatorCategory.HABITACAO,
    unit="%",
    polarity=IndicatorPolarity.lower_is_better,
    description_what=(
        "Percentual de domicílios próprios cujos moradores declararam não ter nenhum "
        "documento que comprove a propriedade do imóvel (escritura, contrato, matrícula "
        "etc.), segundo a PNAD Contínua."
    ),
    description_how=(
        "Quanto menor, maior a segurança jurídica da posse do imóvel para quem mora nele — "
        "um proxy direto de informalidade e irregularidade fundiária, que afeta o acesso a "
        "crédito e a políticas habitacionais que exigem comprovação de propriedade."
    ),
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Domicílios próprios sem documento de propriedade\n\n"
        "Fonte: IBGE, PNAD Contínua anual — tabela SIDRA 7191, variável 10368 (\"Distribuição "
        "percentual dos domicílios próprios\"), classificação 886 (\"Existência de algum "
        "documento que comprove a propriedade do domicílio\"), categoria 47933 (\"Não tem "
        "documento que comprove sua propriedade\").\n\n"
        "Considera apenas domicílios já classificados como próprios — não inclui alugados ou "
        "cedidos, que por definição não têm documento de propriedade em nome do morador."
    ),
)
DOMICILIOS_SEM_DOCUMENTO_PROPRIEDADE_QUERY = SidraQuery(
    table=7191, variable=10368, classifications={886: 47933}
)

DOMICILIOS_AGUA_REDE_GERAL = StaticIndicatorMeta(
    slug="domicilios-agua-rede-geral",
    name="Domicílios com água da rede geral",
    category=IndicatorCategory.SANEAMENTO,
    unit="%",
    polarity=IndicatorPolarity.higher_is_better,
    description_what=(
        "Percentual de domicílios cuja principal fonte de abastecimento de água é a rede "
        "geral de distribuição (não poço, cisterna ou outra fonte alternativa), segundo a "
        "PNAD Contínua."
    ),
    description_how=(
        "Quanto maior, maior a cobertura da rede pública de água tratada — fontes "
        "alternativas (poço, cisterna, fonte) não garantem a mesma qualidade e regularidade "
        "de tratamento que a rede geral."
    ),
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Domicílios com água da rede geral\n\n"
        "Fonte: IBGE, PNAD Contínua anual — tabela SIDRA 6731, variável 9784 (\"Distribuição "
        "percentual dos domicílios\"), classificação 1 (\"Situação do domicílio\"), categoria "
        "6795 (\"Total\", urbano + rural) e classificação 825 (\"Principal fonte de "
        "abastecimento de água\"), categoria 46285 (\"Rede geral de distribuição\")."
    ),
)
DOMICILIOS_AGUA_REDE_GERAL_QUERY = SidraQuery(table=6731, variable=9784, classifications={1: 6795, 825: 46285})

DOMICILIOS_ESGOTO_REDE_GERAL = StaticIndicatorMeta(
    slug="domicilios-esgoto-rede-geral",
    name="Domicílios com esgotamento sanitário adequado",
    category=IndicatorCategory.SANEAMENTO,
    unit="%",
    polarity=IndicatorPolarity.higher_is_better,
    description_what=(
        "Percentual de domicílios cujo esgoto é escoado para rede geral (coletora) ou rede "
        "pluvial, segundo a PNAD Contínua — não inclui fossa séptica não ligada à rede, fossa "
        "rudimentar ou despejo direto em rio/mar/valão."
    ),
    description_how=(
        "É historicamente o indicador de saneamento com maior disparidade regional no Brasil "
        "— quanto maior, maior a cobertura de coleta formal de esgoto, com impacto direto na "
        "saúde pública (redução de doenças de veiculação hídrica)."
    ),
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Domicílios com esgotamento sanitário adequado\n\n"
        "Fonte: IBGE, PNAD Contínua anual — tabela SIDRA 7192, variável 9988 (\"Distribuição "
        "percentual dos domicílios com banheiro, sanitário ou buraco para dejeções\"), "
        "classificação 1 (\"Situação do domicílio\"), categoria 6795 (\"Total\") e "
        "classificação 11558 (\"Tipo de esgotamento sanitário\"), categoria 47930 (\"Rede "
        "geral ou rede pluvial\").\n\n"
        "A tabela só existe a partir de 2019 no SIDRA (antes disso, o IBGE publicava a "
        "pergunta com categorias diferentes, tabela 6735, não comparável diretamente)."
    ),
)
DOMICILIOS_ESGOTO_REDE_GERAL_QUERY = SidraQuery(
    table=7192, variable=9988, classifications={1: 6795, 11558: 47930}
)

DOMICILIOS_LIXO_COLETADO = StaticIndicatorMeta(
    slug="domicilios-lixo-coletado",
    name="Domicílios com coleta de lixo",
    category=IndicatorCategory.SANEAMENTO,
    unit="%",
    polarity=IndicatorPolarity.higher_is_better,
    description_what=(
        "Percentual de domicílios cujo lixo é coletado diretamente por serviço de limpeza "
        "urbana (não inclui coleta em caçamba comunitária, queima na propriedade ou outro "
        "destino), segundo a PNAD Contínua."
    ),
    description_how=(
        "Quanto maior, maior a cobertura do serviço público de coleta domiciliar de lixo — "
        "queima ou descarte irregular tem impacto direto em saúde pública e meio ambiente."
    ),
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Domicílios com coleta de lixo\n\n"
        "Fonte: IBGE, PNAD Contínua anual — tabela SIDRA 6736, variável 9784, classificação 1 "
        "(\"Situação do domicílio\"), categoria 6795 (\"Total\") e classificação 67 (\"Destino "
        "do lixo\"), categoria 4661 (\"Coletado diretamente por serviço de limpeza\")."
    ),
)
DOMICILIOS_LIXO_COLETADO_QUERY = SidraQuery(table=6736, variable=9784, classifications={1: 6795, 67: 4661})

DOMICILIOS_ENERGIA_ELETRICA = StaticIndicatorMeta(
    slug="domicilios-energia-eletrica",
    name="Domicílios com energia elétrica em tempo integral",
    category=IndicatorCategory.INFRAESTRUTURA,
    unit="%",
    polarity=IndicatorPolarity.higher_is_better,
    description_what=(
        "Percentual de domicílios que têm energia elétrica proveniente da rede geral em "
        "tempo integral (24 horas por dia), segundo a PNAD Contínua."
    ),
    description_how=(
        "O Brasil já tem cobertura elétrica quase universal — este indicador é mais útil para "
        "identificar os bolsões residuais sem acesso (áreas rurais isoladas, comunidades "
        "ribeirinhas) do que para acompanhar tendência nacional, que se move pouco de um ano "
        "para o outro."
    ),
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Domicílios com energia elétrica em tempo integral\n\n"
        "Fonte: IBGE, PNAD Contínua anual — tabela SIDRA 6738, variável 9994 (\"Percentual de "
        "domicílios com energia elétrica proveniente de rede geral em tempo integral\"), "
        "classificação 1 (\"Situação do domicílio\"), categoria 6795 (\"Total\")."
    ),
)
DOMICILIOS_ENERGIA_ELETRICA_QUERY = SidraQuery(table=6738, variable=9994, classifications={1: 6795})

DOMICILIOS_COM_INTERNET = StaticIndicatorMeta(
    slug="domicilios-com-internet",
    name="Domicílios com acesso à internet",
    category=IndicatorCategory.INFRAESTRUTURA,
    unit="%",
    polarity=IndicatorPolarity.higher_is_better,
    description_what=(
        "Percentual de domicílios em que havia utilização de internet, segundo a PNAD "
        "Contínua — não distingue qualidade ou velocidade da conexão, só se havia acesso."
    ),
    description_how=(
        "Quanto maior, maior a proporção de domicílios com acesso à internet — hoje um "
        "insumo básico para trabalho, estudo e acesso a serviços públicos digitais. Ainda "
        "existe uma diferença relevante entre estados."
    ),
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Domicílios com acesso à internet\n\n"
        "Fonte: IBGE, PNAD Contínua anual — tabela SIDRA 7307, variável 9784 (\"Distribuição "
        "percentual dos domicílios\"), classificação 1 (\"Situação do domicílio\"), categoria "
        "6795 (\"Total\") e classificação 688 (\"Existência de utilização da Internet no "
        "domicílio\"), categoria 48534 (\"Havia utilização de internet\")."
    ),
)
DOMICILIOS_COM_INTERNET_QUERY = SidraQuery(table=7307, variable=9784, classifications={1: 6795, 688: 48534})

VALOR_PRODUCAO_AGRICOLA = StaticIndicatorMeta(
    slug="valor-producao-agricola",
    name="Valor da produção agrícola",
    category=IndicatorCategory.AGRICULTURA,
    unit="R$ mil",
    polarity=IndicatorPolarity.neutral,
    description_what=(
        "Valor total da produção das lavouras temporárias (soja, milho, cana etc.) e "
        "permanentes (café, laranja etc.), a preços correntes de cada ano, segundo o IBGE."
    ),
    description_how=(
        "Não é classificado como melhora/piora — o valor varia tanto pela quantidade "
        "produzida quanto pelo preço internacional das commodities agrícolas, que o governo "
        "brasileiro não controla diretamente. Uma queda pode refletir preços internacionais "
        "mais baixos numa safra recorde, e não necessariamente um problema de produção."
    ),
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Valor da produção agrícola\n\n"
        "Fonte: IBGE, Produção Agrícola Municipal (PAM) — tabela SIDRA 5457, variável 215 "
        "(\"Valor da produção\"), classificação 782 (\"Produto das lavouras temporárias e "
        "permanentes\"), categoria 0 (\"Total\").\n\n"
        "A série da tabela começa em 1974, mas mudou de moeda várias vezes antes do Plano "
        "Real (Cruzeiro, Cruzado, Cruzado Novo, Cruzeiro Real) — o IFB só exibe valores a "
        "partir de 1994 (\"Mil Reais\"), quando a série passa a usar uma moeda única e "
        "estável, comparável ano a ano sem correção manual."
    ),
)
VALOR_PRODUCAO_AGRICOLA_QUERY = SidraQuery(table=5457, variable=215, classifications={782: 0})

PRODUCAO_INDUSTRIAL = StaticIndicatorMeta(
    slug="producao-industrial",
    name="Produção industrial (variação interanual)",
    category=IndicatorCategory.INDUSTRIA,
    unit="%",
    polarity=IndicatorPolarity.higher_is_better,
    description_what=(
        "Variação mensal do índice de produção física da indústria geral (extrativa + "
        "transformação), em relação ao mesmo mês do ano anterior, segundo a Pesquisa "
        "Industrial Mensal de Produção Física (PIM-PF) do IBGE."
    ),
    description_how=(
        "É a mesma taxa amplamente divulgada como \"produção industrial\" nos anúncios "
        "mensais do IBGE. Positivo indica que a indústria produziu mais do que no mesmo mês "
        "do ano anterior; negativo indica retração."
    ),
    update_frequency="mensal",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Produção industrial (variação interanual)\n\n"
        "Fonte: IBGE, Pesquisa Industrial Mensal - Produção Física (PIM-PF) — tabela SIDRA "
        "8888, variável 11602 (\"Variação mês/mesmo mês do ano anterior (M/M-12)\"), "
        "classificação 544 (\"Seções e atividades industriais\"), categoria 129314 (\"1 "
        "Indústria geral\").\n\n"
        "A pesquisa por estado não cobre todas as 27 unidades da federação — só os estados "
        "com representatividade industrial suficiente para a amostra do IBGE. O IFB não "
        "inventa um valor para os estados sem cobertura; eles simplesmente não aparecem na "
        "comparação por estado."
    ),
)
PRODUCAO_INDUSTRIAL_QUERY = SidraQuery(table=8888, variable=11602, classifications={544: 129314})

DOMICILIOS_BOLSA_FAMILIA = StaticIndicatorMeta(
    slug="domicilios-bolsa-familia",
    name="Domicílios que recebem Bolsa Família",
    category=IndicatorCategory.ASSISTENCIA_SOCIAL,
    unit="mil domicílios",
    polarity=IndicatorPolarity.neutral,
    description_what=(
        "Número de domicílios em que algum morador recebeu rendimento do Programa Bolsa "
        "Família (ou seu antecessor/sucessor sob outro nome, conforme vigente no ano), "
        "segundo a PNAD Contínua."
    ),
    description_how=(
        "Não é classificado como melhora/piora — uma alta pode significar tanto expansão "
        "deliberada do programa (mais famílias cobertas) quanto mais famílias em situação de "
        "pobreza que passaram a ter direito ao benefício, dependendo do contexto econômico e "
        "de regras de elegibilidade do período. É uma contagem absoluta (não uma taxa), então "
        "estados mais populosos tendem a ter números maiores mesmo com cobertura "
        "proporcionalmente menor — compare sempre relativizando pelo tamanho do estado."
    ),
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Domicílios que recebem Bolsa Família\n\n"
        "Fonte: IBGE, PNAD Contínua anual — tabela SIDRA 7449, variável 10790 (\"Domicílios "
        "em que algum morador do domicílio recebeu rendimento do Programa Bolsa Família\"), "
        "classificação 1032 (\"Posse ou acesso a bens ou serviços\"), categoria 49236 "
        "(\"Total\").\n\n"
        "É a contagem de domicílios (a pergunta da PNAD Contínua usa o nome do programa "
        "vigente na data da entrevista), não o número de pessoas nem de famílias cadastradas "
        "no CadÚnico — pode diferir dos números oficiais do Ministério do Desenvolvimento e "
        "Assistência Social, que usa a folha de pagamento administrativa do programa como "
        "fonte, não uma pesquisa amostral."
    ),
)
DOMICILIOS_BOLSA_FAMILIA_QUERY = SidraQuery(table=7449, variable=10790, classifications={1032: 49236})

RAZAO_RENDIMENTO_MULHER_HOMEM = StaticIndicatorMeta(
    slug="razao-rendimento-mulher-homem",
    name="Razão de rendimento entre mulheres e homens",
    category=IndicatorCategory.MULHERES,
    unit="% do rendimento dos homens",
    polarity=IndicatorPolarity.higher_is_better,
    description_what=(
        "Rendimento médio mensal real habitual das mulheres ocupadas, como percentual do "
        "rendimento médio dos homens ocupados, segundo a PNAD Contínua. Quanto mais perto de "
        "100%, menor a diferença salarial entre os sexos."
    ),
    description_how=(
        "Quanto maior, menor a disparidade salarial entre mulheres e homens. Não isola o "
        "efeito de cargo, escolaridade ou setor de atuação — é a diferença bruta observada no "
        "mercado de trabalho como um todo, um retrato do resultado agregado, não uma medida "
        "de discriminação direta em uma função idêntica."
    ),
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Razão de rendimento entre mulheres e homens\n\n"
        "Fonte: IBGE, PNAD Contínua anual — tabela SIDRA 10377, variável 5933 (\"Rendimento "
        "médio mensal real... habitualmente recebido em todos os trabalhos\"), classificação "
        "2 (\"Sexo\"), categorias 4 (\"Homens\") e 5 (\"Mulheres\").\n\n"
        "O IFB busca as duas séries (rendimento de homens e de mulheres) separadamente e "
        "calcula a razão mulheres/homens em cada ano — a própria tabela do SIDRA não traz "
        "essa razão pronta. O cálculo é feito no sync (`app/sync/run.py`), não no cliente "
        "SIDRA, que continua devolvendo cada série sem transformação."
    ),
)
RENDIMENTO_HOMENS_QUERY = SidraQuery(table=10377, variable=5933, classifications={2: 4})
RENDIMENTO_MULHERES_QUERY = SidraQuery(table=10377, variable=5933, classifications={2: 5})

TAXA_FREQUENCIA_PRE_ESCOLA = StaticIndicatorMeta(
    slug="taxa-frequencia-pre-escola",
    name="Taxa de frequência à creche ou escola (4 a 5 anos)",
    category=IndicatorCategory.CRIANCAS,
    unit="%",
    polarity=IndicatorPolarity.higher_is_better,
    description_what=(
        "Percentual de crianças de 4 a 5 anos de idade que frequentam creche ou escola "
        "(pré-escola), segundo a PNAD Contínua — a faixa etária em que a Constituição prevê "
        "acesso obrigatório à educação básica no Brasil."
    ),
    description_how=(
        "Quanto maior, mais perto da universalização do acesso à pré-escola, meta "
        "constitucional desde a Emenda 59/2009. Não tem quebra por estado disponível nesta "
        "tabela do IBGE — só Brasil e grandes regiões."
    ),
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Taxa de frequência à creche ou escola (4 a 5 anos)\n\n"
        "Fonte: IBGE, PNAD Contínua anual — tabela SIDRA 7140, variável 10280 (\"Distribuição "
        "percentual das crianças de 0 a 5 anos de idade\"), classificação 58 (\"Grupo de "
        "idade\"), categoria 47813 (\"4 a 5 anos\") e classificação 12081 (\"Frequência à "
        "creche ou escola\"), categoria 47810 (\"Frequenta escola ou creche\").\n\n"
        "A tabela do IBGE só tem nível Brasil e Grandes Regiões (N1/N2) — não há quebra por "
        "estado disponível nesta pesquisa."
    ),
)
TAXA_FREQUENCIA_PRE_ESCOLA_QUERY = SidraQuery(table=7140, variable=10280, classifications={58: 47813, 12081: 47810})

TAXA_TRABALHO_INFANTIL = StaticIndicatorMeta(
    slug="taxa-trabalho-infantil",
    name="Taxa de trabalho infantil (5 a 17 anos)",
    category=IndicatorCategory.CRIANCAS,
    unit="%",
    polarity=IndicatorPolarity.lower_is_better,
    description_what=(
        "Percentual de crianças e adolescentes de 5 a 17 anos de idade em situação de "
        "trabalho infantil, segundo a definição da Organização Internacional do Trabalho "
        "(OIT) — inclui trabalho remunerado ou não, em atividade econômica, mesmo que "
        "informal ou dentro de casa."
    ),
    description_how=(
        "Quanto menor, melhor. A pesquisa é um suplemento especial da PNAD Contínua, não "
        "aplicado todo ano — não há dado para 2020 e 2021 (suspenso durante a pandemia). O "
        "IBGE classifica como 'Estatísticas experimentais', metodologia ainda em consolidação. "
        "Não tem quebra por estado disponível — só Brasil."
    ),
    update_frequency="anual (com interrupções)",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Taxa de trabalho infantil (5 a 17 anos)\n\n"
        "Fonte: IBGE, PNAD Contínua, suplemento de Trabalho Infantil — tabela SIDRA 9831, "
        "variável 9489 (\"Percentual de pessoas de 5 a 17 anos de idade em situação de "
        "trabalho infantil\"), classificação 58 (\"Grupo de idade\"), categoria 95253 "
        "(\"Total\") e classificação 2 (\"Sexo\"), categoria 6794 (\"Total\"). Estatística "
        "experimental do IBGE (Indicador ODS 8.7.1 tem definição mais restrita e não é usado "
        "aqui — diverge do número amplamente noticiado).\n\n"
        "A tabela do IBGE só tem nível Brasil (N1) — não há quebra por estado nesta pesquisa.\n\n"
        "Conferido: 2022 = 4,9%, 2023 = 4,2%, mesmos números já noticiados amplamente na "
        "imprensa a partir do mesmo levantamento do IBGE."
    ),
)
TAXA_TRABALHO_INFANTIL_QUERY = SidraQuery(table=9831, variable=9489, classifications={58: 95253, 2: 6794})

RAZAO_DEPENDENCIA_IDOSOS = StaticIndicatorMeta(
    slug="razao-dependencia-idosos",
    name="Razão de dependência de idosos",
    category=IndicatorCategory.IDOSOS,
    unit="idosos por 100 pessoas em idade ativa",
    polarity=IndicatorPolarity.neutral,
    description_what=(
        "Número de pessoas de 65 anos ou mais para cada 100 pessoas em idade ativa (15 a 64 "
        "anos), segundo a Projeção da População do IBGE."
    ),
    description_how=(
        "Não é classificado como melhora/piora — reflete a transição demográfica estrutural "
        "do país (mais esperança de vida, menos nascimentos), com implicações diretas para o "
        "sistema previdenciário e a demanda por saúde e cuidados de longa duração, mas que vão "
        "muito além de um único governo."
    ),
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Razão de dependência de idosos\n\n"
        "Fonte: IBGE, Projeção da População — tabela SIDRA 7360, variável 10611. Mesma tabela "
        "já usada para nascimentos, óbitos e índice de envelhecimento (indicador "
        "`indice-envelhecimento`) — diferente deste, que é uma proporção sobre o total de "
        "crianças, a razão de dependência de idosos é sobre a população em idade ativa, "
        "métrica mais direta para debates sobre sustentabilidade previdenciária."
    ),
)
RAZAO_DEPENDENCIA_IDOSOS_QUERY = SidraQuery(table=7360, variable=10611, classifications={1933: "all"})

INDICE_GINI_PIB_MUNICIPAL = StaticIndicatorMeta(
    slug="indice-gini-pib-municipal",
    name="Índice de Gini da distribuição do PIB municipal",
    category=IndicatorCategory.DESENVOLVIMENTO_REGIONAL,
    unit="índice (0 a 1)",
    polarity=IndicatorPolarity.lower_is_better,
    description_what=(
        "Medida de concentração do Produto Interno Bruto entre os municípios — no Brasil, "
        "mede o quanto o PIB nacional está concentrado em poucos municípios; em cada estado, "
        "mede o quanto o PIB estadual está concentrado em poucos municípios daquele estado. "
        "Varia de 0 (PIB distribuído igualmente entre todos os municípios) a 1 (totalmente "
        "concentrado em um único município)."
    ),
    description_how=(
        "Quanto menor, mais distribuído territorialmente é o desenvolvimento econômico — um "
        "índice alto indica que a atividade econômica está concentrada em poucos polos "
        "(normalmente a capital ou uma região metropolitana), com o restante do território "
        "pouco desenvolvido em comparação. Não tem valor para o Distrito Federal (é um único "
        "município, não há distribuição a medir)."
    ),
    update_frequency="anual",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Índice de Gini da distribuição do PIB municipal\n\n"
        "Fonte: IBGE, Produto Interno Bruto dos Municípios — tabela SIDRA 5939, variável 529 "
        "(\"Índice de Gini da distribuição do produto interno bruto a preços correntes\")."
    ),
)
INDICE_GINI_PIB_MUNICIPAL_QUERY = SidraQuery(table=5939, variable=529, classifications={})

SOURCE_CNJ = SourceSpec(
    key="cnj",
    name="Conselho Nacional de Justiça (DataJud)",
    url="https://datajud-wiki.cnj.jus.br/api-publica/",
    description="Conselho Nacional de Justiça — base nacional de dados do Poder Judiciário (DataJud).",
)

PROCESSOS_AJUIZADOS_ESTADUAL = StaticIndicatorMeta(
    slug="processos-ajuizados-estadual",
    name="Processos ajuizados na Justiça estadual",
    category=IndicatorCategory.JUSTICA,
    unit="processos",
    polarity=IndicatorPolarity.neutral,
    description_what=(
        "Número de novos processos judiciais ajuizados no ano nos Tribunais de Justiça "
        "estaduais (1º e 2º graus, todos os ramos de competência) — não inclui Justiça "
        "Federal, do Trabalho, Eleitoral, Militar nem os tribunais superiores (STJ, TST, TSE, "
        "STF), que têm bases próprias não cobertas por este indicador."
    ),
    description_how=(
        "Não é classificado como melhora/piora — mais processos pode significar tanto maior "
        "acesso da população à Justiça quanto mais conflitos na sociedade, e menos processos "
        "pode refletir tanto menor litigiosidade quanto barreiras de acesso. É uma contagem "
        "absoluta, então estados mais populosos tendem a ter números maiores."
    ),
    update_frequency="anual",
    source=SOURCE_CNJ,
    methodology=(
        "# Metodologia — Processos ajuizados na Justiça estadual\n\n"
        "Fonte: CNJ, API Pública do DataJud (`api-publica.datajud.cnj.jus.br`) — base nacional "
        "de metadados processuais do Judiciário, alimentada diretamente pelos sistemas dos "
        "tribunais. O IFB consulta, para cada um dos 27 Tribunais de Justiça estaduais, uma "
        "agregação de contagem (não baixa processo nenhum) filtrando pelo campo "
        "`dataAjuizamento` dentro do ano de referência, e soma os 27 totais para o valor "
        "Brasil.\n\n"
        "A API do DataJud usa uma chave pública compartilhada, documentada oficialmente pelo "
        "próprio CNJ para uso livre por qualquer aplicação (não é uma credencial do IFB) — o "
        "CNJ pode trocar essa chave a qualquer momento, o que interromperia a sincronização "
        "deste indicador até a atualização da chave em `app/sync/datajud_client.py`.\n\n"
        "Cobre só a Justiça estadual (Tribunais de Justiça) — Justiça Federal, do Trabalho, "
        "Eleitoral, Militar e tribunais superiores têm bases próprias no DataJud, não "
        "agregadas aqui nesta primeira versão do indicador."
    ),
)

_RREO_FUNCAO_METHODOLOGY_NOTE = (
    "**Sobre a apuração**: o Relatório Resumido de Execução Orçamentária (RREO) é declarado "
    "pelo próprio ente ao Tesouro Nacional a cada bimestre, conforme exigido pela Lei de "
    "Responsabilidade Fiscal (LRF). O IFB sincroniza sempre o fechamento do 6º bimestre (valor "
    "acumulado no exercício inteiro). Não há dado disponível no SICONFI para exercícios "
    "anteriores a 2015."
)

DESPESA_EDUCACAO_ESTADUAL = StaticIndicatorMeta(
    slug="despesa-educacao-estadual",
    name="Despesa com Educação (% do total de despesas)",
    category=IndicatorCategory.GESTAO_PUBLICA,
    unit="% do total de despesas liquidadas",
    polarity=IndicatorPolarity.neutral,
    description_what=(
        "Percentual do total de despesas liquidadas pelo governo estadual no ano que foi "
        "destinado à função Educação (inclui ensino básico, médio, superior, profissional e "
        "encargos gerais da área)."
    ),
    description_how=(
        "Não é classificado como melhora/piora — é uma medida de prioridade orçamentária, não "
        "de qualidade do gasto. A Constituição exige um piso mínimo de investimento em "
        "educação sobre a receita de impostos (não sobre o total de despesas, que é a base "
        "usada aqui), então este percentual não deve ser comparado diretamente com esse piso "
        "constitucional."
    ),
    update_frequency="anual",
    source=SOURCE_SICONFI,
    methodology=(
        "# Metodologia — Despesa com Educação (% do total de despesas)\n\n"
        "Fonte: Tesouro Nacional, SICONFI — Relatório Resumido de Execução Orçamentária "
        "(RREO), Anexo 02 (Demonstrativo das Despesas por Função/Subfunção), conta "
        "\"Educação\", coluna \"% (d/total d)\" (percentual das despesas liquidadas na função "
        "sobre o total de despesas liquidadas até o bimestre).\n\n" + _RREO_FUNCAO_METHODOLOGY_NOTE
    ),
)

DESPESA_SAUDE_ESTADUAL = StaticIndicatorMeta(
    slug="despesa-saude-estadual",
    name="Despesa com Saúde (% do total de despesas)",
    category=IndicatorCategory.GESTAO_PUBLICA,
    unit="% do total de despesas liquidadas",
    polarity=IndicatorPolarity.neutral,
    description_what=(
        "Percentual do total de despesas liquidadas pelo governo estadual no ano que foi "
        "destinado à função Saúde (atenção básica, assistência hospitalar e ambulatorial, "
        "vigilância sanitária e epidemiológica, entre outras)."
    ),
    description_how=(
        "Não é classificado como melhora/piora — é uma medida de prioridade orçamentária, não "
        "de qualidade do gasto. A Constituição exige um piso mínimo de investimento em saúde "
        "sobre a receita de impostos (não sobre o total de despesas, que é a base usada aqui), "
        "então este percentual não deve ser comparado diretamente com esse piso constitucional."
    ),
    update_frequency="anual",
    source=SOURCE_SICONFI,
    methodology=(
        "# Metodologia — Despesa com Saúde (% do total de despesas)\n\n"
        "Fonte: Tesouro Nacional, SICONFI — Relatório Resumido de Execução Orçamentária "
        "(RREO), Anexo 02 (Demonstrativo das Despesas por Função/Subfunção), conta \"Saúde\", "
        "coluna \"% (d/total d)\" (percentual das despesas liquidadas na função sobre o total "
        "de despesas liquidadas até o bimestre).\n\n" + _RREO_FUNCAO_METHODOLOGY_NOTE
    ),
)

INVESTIMENTO_PUBLICO_ESTADUAL = StaticIndicatorMeta(
    slug="investimento-publico-estadual",
    name="Investimento público (% do total de despesas)",
    category=IndicatorCategory.GESTAO_PUBLICA,
    unit="% do total de despesas liquidadas",
    polarity=IndicatorPolarity.higher_is_better,
    description_what=(
        "Percentual do total de despesas liquidadas pelo governo estadual no ano que foi "
        "destinado a Investimentos — obras, equipamentos e outros bens de capital, categoria "
        "econômica distinta de despesas correntes (pessoal, custeio) e de outras despesas de "
        "capital (amortização de dívida, inversões financeiras)."
    ),
    description_how=(
        "Quanto maior, mais o governo está investindo em vez de só cobrir despesas correntes "
        "e financeiras. Não mede a qualidade ou o retorno social do investimento — só o "
        "volume, como fração do orçamento total executado."
    ),
    update_frequency="anual",
    source=SOURCE_SICONFI,
    methodology=(
        "# Metodologia — Investimento público (% do total de despesas)\n\n"
        "Fonte: Tesouro Nacional, SICONFI — Relatório Resumido de Execução Orçamentária "
        "(RREO), Anexo 01 (Balanço Orçamentário), duas contas: \"Investimentos\" e "
        "\"TotalDespesas\", ambas na coluna \"Despesas Liquidadas Até o Bimestre (h)\" "
        "(valor acumulado no ano). Diferente da Despesa com Educação/Saúde (Anexo 02, por "
        "função de governo), Investimentos é uma categoria econômica do Anexo 01 e não tem "
        "coluna de percentual pronta — o IFB calcula `Investimentos ÷ TotalDespesas` no sync "
        "(`app/sync/run.py`), mesmo método já usado para a razão de rendimento mulher/homem.\n\n"
        "**Sem dado antes de 2015**: mesma limitação das demais séries do SICONFI (RGF/RREO) "
        "— o sistema não retroage a exercícios anteriores.\n\n"
        "Conferido: São Paulo 2023 = 4,5% — na faixa historicamente baixa de investimento "
        "público estadual já documentada no debate sobre finanças públicas brasileiras (a "
        "maior parte do orçamento vai para despesas correntes, sobretudo pessoal)."
    ),
)

SOURCE_COMEXSTAT = SourceSpec(
    key="comexstat",
    name="Ministério do Desenvolvimento, Indústria, Comércio e Serviços (Comex Stat)",
    url="https://comexstat.mdic.gov.br/",
    description=(
        "Comex Stat — estatísticas oficiais de comércio exterior brasileiro (exportações e "
        "importações), mantidas pelo MDIC."
    ),
)

EXPORTACOES_TOTAIS = StaticIndicatorMeta(
    slug="exportacoes-totais",
    name="Exportações totais",
    category=IndicatorCategory.COMERCIO_EXTERIOR,
    unit="US$ FOB",
    polarity=IndicatorPolarity.neutral,
    description_what=(
        "Valor total das exportações brasileiras no ano, em dólares FOB (preço da mercadoria "
        "posta a bordo do transporte, sem frete nem seguro internacional)."
    ),
    description_how=(
        "Não é classificado como melhora/piora isolada — varia com o volume exportado, mas "
        "também com o preço internacional das commodities (boa parte da pauta exportadora "
        "brasileira), que o governo não controla diretamente. Compare sempre com as "
        "importações do mesmo período para entender o saldo comercial."
    ),
    update_frequency="anual",
    source=SOURCE_COMEXSTAT,
    methodology=(
        "# Metodologia — Exportações totais\n\n"
        "Fonte: MDIC, Comex Stat — API pública (`api-comexstat.mdic.gov.br`), consulta com "
        "`flow: \"export\"` e métrica `metricFOB`, valor FOB em dólares americanos.\n\n"
        "A API não exige chave de acesso, mas tem um limite de requisições agressivo (a "
        "própria API retorna a mensagem de limite excedido) — o IFB espaça as chamadas do "
        "sync para respeitar esse limite."
    ),
)

IMPORTACOES_TOTAIS = StaticIndicatorMeta(
    slug="importacoes-totais",
    name="Importações totais",
    category=IndicatorCategory.COMERCIO_EXTERIOR,
    unit="US$ FOB",
    polarity=IndicatorPolarity.neutral,
    description_what=(
        "Valor total das importações brasileiras no ano, em dólares FOB (preço da mercadoria "
        "posta a bordo do transporte, sem frete nem seguro internacional)."
    ),
    description_how=(
        "Não é classificado como melhora/piora isolada — um aumento pode refletir tanto maior "
        "atividade econômica interna (mais insumos e bens de capital importados) quanto "
        "pressão cambial desfavorável. Compare sempre com as exportações do mesmo período."
    ),
    update_frequency="anual",
    source=SOURCE_COMEXSTAT,
    methodology=(
        "# Metodologia — Importações totais\n\n"
        "Fonte: MDIC, Comex Stat — API pública (`api-comexstat.mdic.gov.br`), consulta com "
        "`flow: \"import\"` e métrica `metricFOB`, valor FOB em dólares americanos."
    ),
)

SOURCE_MJSP = SourceSpec(
    key="mjsp-sinesp-vde",
    name="Ministério da Justiça e Segurança Pública (Sinesp VDE)",
    url=(
        "https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/"
        "dados-nacionais-1"
    ),
    description=(
        "Ministério da Justiça e Segurança Pública — Base de Dados Nacional de Segurança "
        "Pública (Sinesp VDE), consolidada a partir de dados declarados pelos gestores "
        "estaduais de segurança pública."
    ),
)

HOMICIDIO_DOLOSO_ESTADUAL = StaticIndicatorMeta(
    slug="homicidio-doloso-estadual",
    name="Homicídio doloso",
    category=IndicatorCategory.SEGURANCA,
    unit="ocorrências",
    polarity=IndicatorPolarity.lower_is_better,
    description_what=(
        "Número de vítimas de homicídio doloso (morte intencional, sem incluir latrocínio, "
        "lesão corporal seguida de morte ou mortes decorrentes de intervenção de agente do "
        "Estado, que são categorias separadas nesta mesma base) registradas no ano."
    ),
    description_how=(
        "Quanto menor, menos mortes violentas intencionais no período. É uma contagem "
        "absoluta, então estados mais populosos tendem a ter números maiores — compare "
        "sempre relativizando pelo tamanho do estado, não em valor absoluto."
    ),
    update_frequency="anual",
    source=SOURCE_MJSP,
    methodology=(
        "# Metodologia — Homicídio doloso\n\n"
        "Fonte: Ministério da Justiça e Segurança Pública, Base de Dados Nacional de "
        "Segurança Pública (Sinesp VDE — Validador de Dados Estatísticos). O IFB baixa o "
        "arquivo anual publicado pelo MJSP (um arquivo `.xlsx` por ano, com um registro por "
        "UF/município/tipo de ocorrência/mês) e soma o campo `total_vitima` das linhas com "
        "`evento = \"Homicídio doloso\"`, por UF e por ano.\n\n"
        "Os dados são declarados pelos próprios gestores estaduais de segurança pública ao "
        "MJSP, que os consolida nacionalmente — não é um dado apurado diretamente pelo IFB "
        "nem pelo governo federal. Diferente da Taxa de Mortes Violentas Intencionais "
        "(indicador `taxa-mortes-violentas-intencionais-estadual`, fonte não-governamental "
        "FBSP, que soma homicídio doloso + latrocínio + lesão corporal seguida de morte), "
        "este indicador conta só a categoria \"Homicídio doloso\" isoladamente, direto da "
        "fonte oficial do governo federal."
    ),
)

AREA_ALERTA_DESMATAMENTO_CERRADO = StaticIndicatorMeta(
    slug="area-alerta-desmatamento-cerrado",
    name="Área sob alerta de desmatamento — Cerrado (DETER)",
    category=IndicatorCategory.MEIO_AMBIENTE,
    unit="km²/ano",
    polarity=IndicatorPolarity.lower_is_better,
    description_what=(
        "Área total sob alerta de desmatamento no bioma Cerrado detectada pelo sistema DETER "
        "do INPE, somada por ano civil (janeiro a dezembro)."
    ),
    description_how=(
        "Quanto menor, menos área sob alerta de desmatamento no período. O DETER é um sistema "
        "de **alerta rápido**, não a taxa oficial consolidada de desmatamento (essa é medida "
        "pelo PRODES, que para o Cerrado não está disponível nesta versão do IFB — ver nota "
        "na metodologia) — os números não devem ser somados nem comparados diretamente com o "
        "indicador de desmatamento da Amazônia Legal, que usa o PRODES."
    ),
    update_frequency="anual",
    source=SOURCE_INPE,
    methodology=(
        "# Metodologia — Área sob alerta de desmatamento no Cerrado (DETER)\n\n"
        "Fonte: INPE, sistema DETER (Detecção de Desmatamento em Tempo Real) para o bioma "
        "Cerrado. O IFB coleta o arquivo de alertas mensais agregados por estado, publicado "
        "pelo painel oficial TerraBrasilis (`file-delivery/download/deter-cerrado-nb/monthly`), "
        "e soma os 12 meses de cada ano civil. O ano corrente é sempre excluído por estar "
        "incompleto.\n\n"
        "**Por que DETER e não PRODES para o Cerrado**: o painel oficial do PRODES Cerrado "
        "(distinto do DETER) apresentou um problema técnico confirmado em testes do IFB — a "
        "página específica do Cerrado carrega os dados da Amazônia Legal por engano — então "
        "não foi usado. O DETER cobre o mesmo bioma por um sistema de alerta diferente, "
        "operado pelo mesmo INPE, com dados agregados e publicados corretamente.\n\n"
        "**DETER não é a taxa oficial de desmatamento**: mede alertas detectados por satélite "
        "de forma rápida (dias a semanas), com metodologia de classificação diferente da "
        "consolidação anual do PRODES — os valores costumam diferir entre os dois sistemas "
        "para o mesmo período, e este indicador não deve ser interpretado como \"a taxa de "
        "desmatamento do Cerrado\", só como um indicador de tendência baseado em alertas."
    ),
)

SOURCE_SIOP = SourceSpec(
    key="siop",
    name="Ministério do Planejamento e Orçamento (SIOP)",
    url="https://www1.siop.planejamento.gov.br/siopdoc/doku.php/acesso_publico:dados_abertos",
    description=(
        "Sistema Integrado de Planejamento e Orçamento do Governo Federal (SIOP) — dados "
        "abertos de execução orçamentária da União, publicados em RDF/SPARQL."
    ),
)

EXECUCAO_ORCAMENTARIA_UNIAO = StaticIndicatorMeta(
    slug="execucao-orcamentaria-uniao",
    name="Execução orçamentária da União (valor pago)",
    category=IndicatorCategory.TRANSPARENCIA_CONTROLE,
    unit="R$",
    polarity=IndicatorPolarity.neutral,
    description_what=(
        "Soma de tudo que foi efetivamente pago pelo governo federal no exercício, somando o "
        "valor pago de cada item de despesa do Orçamento Geral da União — inclui despesas "
        "correntes, investimentos, transferências a estados e municípios, e serviço da dívida."
    ),
    description_how=(
        "Não é classificado como melhora/piora — é o tamanho do gasto federal executado, não "
        "uma medida de qualidade ou eficiência do gasto. Cresce naturalmente com a inflação e "
        "com o tamanho da economia; para avaliar se o gasto está crescendo ou encolhendo em "
        "termos reais, é preciso descontar a inflação do período, o que este indicador não "
        "faz."
    ),
    update_frequency="anual",
    source=SOURCE_SIOP,
    methodology=(
        "# Metodologia — Execução orçamentária da União (valor pago)\n\n"
        "Fonte: SIOP (Sistema Integrado de Planejamento e Orçamento do Governo Federal), "
        "endpoint SPARQL público (`www1.siop.planejamento.gov.br/sparql/`) — dados publicados "
        "em RDF pelo próprio Ministério do Planejamento e Orçamento, sem autenticação.\n\n"
        "O IFB soma a propriedade `valorPago` (vocabulário LOA, "
        "`http://vocab.e.gov.br/2013/09/loa#`) de todos os itens de despesa "
        "(`loa:ItemDespesa`) do grafo de cada exercício "
        "(`http://orcamento.dados.gov.br/{ano}/`).\n\n"
        "**Por que o SIOP, e não o Portal da Transparência**: o Portal da Transparência exige "
        "um token pessoal (login gov.br com CPF do usuário) para qualquer chamada à API — o "
        "IFB não usa fontes que dependem de credencial pessoal. O SIOP publica os mesmos "
        "dados de execução orçamentária, sem login, como dado aberto direto da fonte "
        "primária (o próprio Executivo federal, responsável pelo SIOP).\n\n"
        "Validado contra a trajetória amplamente conhecida do orçamento federal: salto de "
        "R$ 2,71 tri (2019) para R$ 3,54 tri (2020, gastos emergenciais da pandemia), subindo "
        "de forma consistente até R$ 4,65 tri (2024)."
    ),
)

PESSOAS_COM_DEFICIENCIA_CENSO_2022 = StaticIndicatorMeta(
    slug="pessoas-com-deficiencia-censo-2022",
    name="Pessoas com deficiência (Censo 2022)",
    category=IndicatorCategory.PESSOAS_COM_DEFICIENCIA,
    unit="% da população de 2 anos ou mais",
    polarity=IndicatorPolarity.neutral,
    description_what=(
        "Percentual da população de 2 anos ou mais de idade identificada como pessoa com "
        "deficiência no Censo Demográfico 2022, segundo os critérios do Grupo de Washington "
        "sobre Estatísticas de Deficiência (avaliação de dificuldade funcional em enxergar, "
        "ouvir, caminhar, memória/concentração e cuidados pessoais)."
    ),
    description_how=(
        "Não é classificado como melhora/piora — é um retrato demográfico, não um resultado "
        "de política pública que muda de um ano para o outro. **Não compare este número com "
        "censos anteriores** (o Censo 2010 usava outra metodologia, sem o Grupo de "
        "Washington, e produzia um percentual muito mais alto) nem com pesquisas amostrais "
        "como a PNS — são instrumentos e critérios diferentes, não a mesma medição em pontos "
        "diferentes do tempo. Só existe o ano de 2022; o próximo ponto de comparação será o "
        "Censo seguinte, daqui a cerca de 10 anos."
    ),
    update_frequency="decenal (Censo)",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Pessoas com deficiência (Censo 2022)\n\n"
        "Fonte: IBGE, Censo Demográfico 2022 — tabela SIDRA 10130, variável 11852 (contagem "
        "de pessoas), classificação 2 (\"Sexo\"), categoria 6794 (\"Total\") e classificação "
        "839 (\"Existência de deficiência\"). O IFB busca a contagem de pessoas com "
        "deficiência e a contagem total separadamente e calcula a razão — a variável "
        "\"Distribuição percentual\" da própria tabela do SIDRA (11856) não serve para isso: "
        "ela é sempre 100% quando filtrada por uma categoria específica de deficiência (é a "
        "distribuição *dentro* do grupo, não em relação ao total da população), mesma "
        "armadilha de combinação de classificações já documentada no indicador "
        "`domicilios-bolsa-familia`.\n\n"
        "**Sobre a metodologia do Censo 2022**: o IBGE adotou pela primeira vez o conjunto "
        "curto de perguntas do Grupo de Washington sobre Estatísticas de Deficiência — uma "
        "mudança amplamente noticiada, porque produziu um percentual de pessoas com "
        "deficiência muito menor do que o Censo 2010 (que usava outra metodologia). Não é "
        "uma queda real na prevalência de deficiência no país, é uma mudança na forma de "
        "medir — por isso este indicador é publicado isoladamente, sem tentar formar uma "
        "série histórica com censos anteriores ou com outras pesquisas (ex: PNS), que usam "
        "instrumentos diferentes.\n\n"
        "Validado ao vivo contra a ordem de grandeza amplamente divulgada na cobertura do "
        "Censo 2022: 14.400.869 pessoas com deficiência em 198.348.756 pessoas de 2 anos ou "
        "mais (7,3% do total)."
    ),
)
PESSOAS_COM_DEFICIENCIA_QUERY = SidraQuery(table=10130, variable=11852, classifications={2: 6794, 839: 58765})
PESSOAS_TOTAL_2_ANOS_OU_MAIS_QUERY = SidraQuery(table=10130, variable=11852, classifications={2: 6794, 839: 46583})

TAXA_OCUPACAO_PESSOAS_COM_DEFICIENCIA = StaticIndicatorMeta(
    slug="taxa-ocupacao-pessoas-com-deficiencia",
    name="Nível de ocupação de pessoas com deficiência",
    category=IndicatorCategory.PESSOAS_COM_DEFICIENCIA,
    unit="%",
    polarity=IndicatorPolarity.higher_is_better,
    description_what=(
        "Percentual de pessoas com deficiência de 14 anos ou mais de idade que estavam "
        "ocupadas (trabalhando) na semana de referência da pesquisa."
    ),
    description_how=(
        "Quanto maior, melhor — mais perto do nível de ocupação da população sem "
        "deficiência (60,7% em 2022, contra 26,6% das pessoas com deficiência, segundo o "
        "mesmo levantamento). Pesquisa suplementar da PNAD Contínua feita uma única vez, em "
        "2022 — não há série histórica nem garantia de repetição periódica."
    ),
    update_frequency="único (módulo especial de 2022)",
    source=SOURCE_IBGE,
    methodology=(
        "# Metodologia — Nível de ocupação de pessoas com deficiência\n\n"
        "Fonte: IBGE, PNAD Contínua — módulo especial \"Pessoas com Deficiência 2022\" "
        "(3º trimestre de 2022), tabela SIDRA 4177, variável 4097 (\"Nível da ocupação, na "
        "semana de referência, das pessoas de 14 anos ou mais de idade\"), classificação 2 "
        "(\"Sexo\"), categoria 6794 (\"Total\"), e classificação 839 (\"Existência de "
        "deficiência\"), categoria 58765 (\"Pessoa com deficiência\").\n\n"
        "Diferente do indicador `pessoas-com-deficiencia-censo-2022` (que vem do Censo "
        "Demográfico, usa a metodologia do Grupo de Washington e mede prevalência), este "
        "indicador vem de uma pesquisa amostral diferente (PNAD Contínua) com seu próprio "
        "critério de identificação de deficiência — os dois não são diretamente comparáveis.\n\n"
        "Conferido: Brasil 2022 = 26,6%, mesmo número já divulgado pelo IBGE na publicação do "
        "módulo."
    ),
)
TAXA_OCUPACAO_PESSOAS_COM_DEFICIENCIA_QUERY = SidraQuery(
    table=4177, variable=4097, classifications={2: 6794, 839: 58765}
)

SOURCE_PNCP = SourceSpec(
    key="pncp",
    name="Portal Nacional de Contratações Públicas (PNCP)",
    url="https://pncp.gov.br/",
    description=(
        "Portal Nacional de Contratações Públicas — base oficial de publicação de "
        "contratações do poder público (Lei 14.133/2021), mantida pela Controladoria-Geral "
        "da União."
    ),
)

VALOR_CONTRATACOES_PREGAO_ELETRONICO = StaticIndicatorMeta(
    slug="valor-contratacoes-pregao-eletronico",
    name="Valor de contratações públicas — Pregão Eletrônico",
    category=IndicatorCategory.COMPRAS_PUBLICAS,
    unit="R$",
    polarity=IndicatorPolarity.neutral,
    description_what=(
        "Soma do valor total estimado das contratações públicas publicadas no PNCP sob a "
        "modalidade Pregão Eletrônico — a modalidade mais comum de compra pública no Brasil "
        "(leilão eletrônico reverso para bens e serviços comuns), por qualquer ente federativo "
        "(municípios, estados e União)."
    ),
    description_how=(
        "Não é classificado como melhora/piora — é o volume de contratações publicadas, não "
        "uma medida de eficiência, economicidade ou regularidade do gasto. **Cobre só uma "
        "modalidade de contratação** (Pregão Eletrônico) — não inclui Dispensa de Licitação, "
        "Concorrência, Inexigibilidade e as demais modalidades previstas na Lei 14.133/2021, "
        "então não deve ser lido como \"o total de compras públicas do Brasil\"."
    ),
    update_frequency="anual",
    source=SOURCE_PNCP,
    methodology=(
        "# Metodologia — Valor de contratações públicas (Pregão Eletrônico)\n\n"
        "Fonte: PNCP (Portal Nacional de Contratações Públicas), API pública de consulta "
        "(`pncp.gov.br/api/consulta`), sem chave de acesso.\n\n"
        "**Acumulação incremental, não tempo real**: o PNCP não expõe nenhum total agregado "
        "pronto — só registros individuais paginados (até 50 por página; uma única semana de "
        "Pregão Eletrônico já tem milhares de registros). Para nunca precisar consultar o "
        "PNCP em tempo real a cada requisição de usuário, o IFB acumula os totais "
        "localmente: a cada sync, busca só os registros publicados desde a última execução "
        "e **soma** ao total já acumulado (tabelas internas `pncp_sync_checkpoints` e "
        "`pncp_contratacao_totals`, ver `app/sync/pncp_client.py`) — nunca refaz a soma do "
        "histórico inteiro do zero. O ano de referência de cada registro é o ano de "
        "`dataPublicacaoPncp` (data em que a contratação foi publicada no portal).\n\n"
        "**Escopo desta primeira versão**: só a modalidade \"Pregão Eletrônico\" (código 6 "
        "na tabela de domínio do PNCP) — a mais comum, mas não a única. Não há registro "
        "publicado no PNCP anterior a 2021 (Lei 14.133/2021, que criou essa obrigatoriedade)."
    ),
)
