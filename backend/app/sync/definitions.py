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
