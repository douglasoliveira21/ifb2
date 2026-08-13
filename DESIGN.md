---
name: Instituto Fiscaliza Brasil
description: Fiscalizamos resultados, não discursos.
colors:
  yellow:
    value: "#f5c400"
  ink:
    value: "#111111"
  paper:
    value: "#ffffff"
  gray-50:
    value: "#f6f6f3"
  gray-100:
    value: "#ececE7"
  gray-500:
    value: "#656565"
  positive:
    value: "#1f7a3d"
  negative:
    value: "#b3261e"
  neutral:
    value: "#656565"
typography:
  display:
    fontFamily: "Inter, Arial, Helvetica, sans-serif"
    fontVariationSettings: "tabular-nums"
    fontWeight: 700
    letterSpacing: "-0.02em"
    lineHeight: 0.95
  body:
    fontFamily: "Inter, Arial, Helvetica, sans-serif"
    fontWeight: 400
  label:
    fontFamily: "Inter, Arial, Helvetica, sans-serif"
    fontWeight: 600
    letterSpacing: "0.05em"
rounded:
  none: "0px"
spacing:
  sm: "8px"
  md: "16px"
  lg: "24px"
components:
  button-primary:
    backgroundColor: "{colors.yellow}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "8px 16px"
  button-primary-hover:
    backgroundColor: "{colors.yellow}"
  badge-melhorou:
    textColor: "{colors.positive}"
  badge-piorou:
    textColor: "{colors.negative}"
  badge-neutro:
    textColor: "{colors.neutral}"
---

# Design System: Instituto Fiscaliza Brasil (IFB)

## Overview

**Creative North Star: "O Placar Editorial"**

O IFB parece a página de um jornal impresso que virou um placar esportivo — não um dashboard de SaaS. A hierarquia vem de tipografia grande e algarismos tabulares (`.stat-figure`, `font-variant-numeric: tabular-nums`), não de cards flutuando em sombra. Divisões entre blocos são linhas finas de 1px (`border-ink`, `border-gray-100`), nunca superfícies elevadas — o layout inteiro é plano, deliberadamente.

O amarelo `#F5C400` é usado como grifo, não como fundo padrão: aparece no logotipo, em CTAs pontuais ("Apoiar o IFB") e em destaques de foco — nunca como cor de fundo de uma seção inteira. A tinta `#111111` carrega quase todo o peso visual (texto, bordas, ícones), reforçando a leitura de "documento oficial" em vez de "produto". Classificações (melhorou/piorou/estável) nunca dependem só de cor — sempre vêm com um glifo geométrico (▲ ▼ ■) e o texto por extenso, para acessibilidade e para honestidade editorial.

Rejeições confirmadas pelo código existente: nenhum `border-radius`, nenhum `box-shadow`, nenhum glassmorphism/blur, nenhuma cor de fundo colorida em blocos inteiros, nenhum ícone de biblioteca (Lucide/Heroicons) — os poucos símbolos usados são glifos Unicode simples.

**Key Characteristics:**
- Tipografia como hierarquia primária — não cor, não sombra, não profundidade.
- Zero elevação: o site é fisicamente plano, como papel.
- Cantos sempre retos (0px de raio) em qualquer superfície ou botão.
- Amarelo é escasso e intencional; tinta preta é o peso visual dominante.
- Classificação nunca é só cor — sempre ícone geométrico + texto.

## Colors

Paleta quase monocromática (tinta sobre papel) com um único acento amarelo e três cores semânticas estritamente funcionais.

### Primary
- **Grifo Amarelo** (`#F5C400`): logotipo, CTA de apoio/doação, estados de foco sobre fundo escuro, destaques pontuais. Nunca cobre uma seção inteira — é usado em elementos pequenos e específicos (**The Rare Yellow Rule**: se o amarelo aparece em mais de ~10% da viewport, está sendo mal usado).

### Neutral
- **Tinta** (`#111111`): texto primário, bordas estruturais (`border-ink`), fundo do selo "IFB" no header, cor de foco visível (`outline: 2px solid var(--color-ink)`, escolhida deliberadamente em vez do azul padrão do navegador para manter contraste sobre botões amarelos).
- **Papel** (`#FFFFFF`): fundo padrão de toda a interface.
- **Neblina Clara** (`#F6F6F3`, `gray-50`): fundo de seções alternadas/sutis.
- **Linha Fina** (`#ECECE7`, `gray-100`): bordas divisórias entre blocos internos (ex: separadores de coluna no Placar Brasil).
- **Cinza Texto Secundário** (`#656565`, `gray-500`): legendas, metadados, texto de apoio. Foi escurecido a partir do `#737373` original da identidade porque falhava WCAG AA (4.37:1) em texto pequeno — `#656565` atinge ≥4.5:1 em qualquer fundo do site. **The Never-Redo-The-Contrast-Fix Rule**: não reverter para `#737373` nem tons mais claros que `#656565` em texto de corpo.

### Semantic (sempre acompanhadas de ícone + texto, nunca só cor)
- **Verde Melhora** (`#1F7A3D`, `positive`): classificação "Melhorou" — sempre junto do glifo ▲.
- **Vermelho Piora** (`#B3261E`, `negative`): classificação "Piorou" — sempre junto do glifo ▼.
- **Neutro** (`#656565`, `neutral`): classificação "Estável"/"Inconclusivo"/"Sem dados" — sempre junto do glifo ■ ou … e do texto por extenso.

### Named Rules
**The One Voice Rule.** O amarelo é o único acento cromático do sistema — não introduzir uma segunda cor de marca (azul, roxo, gradiente) para "diferenciar" uma seção nova.
**The Color-Is-Never-Alone Rule.** Nenhuma informação (melhorou/piorou/status) pode depender só da cor — sempre par com ícone geométrico e rótulo textual.

## Typography

**Display/Body Font:** Inter (via `next/font/google`, variável `--font-inter`), com fallback `Arial, Helvetica, sans-serif`.

**Character:** Uma única família tipográfica para tudo — a hierarquia vem de peso, tamanho e `letter-spacing`, não de mistura de fontes. Números grandes usam `font-variant-numeric: tabular-nums` para alinhar como uma tabela de placar esportivo, com `letter-spacing: -0.02em` e `line-height: 0.95` (classe utilitária `.stat-figure`).

### Hierarchy
- **Stat Figure** (peso 700 `font-bold`, `text-5xl` a `text-6xl`, `line-height: 0.95`, `letter-spacing: -0.02em`, tabular-nums): o elemento tipográfico primário do IFB — o número de um indicador. Usado no Placar Brasil e nas páginas de indicador.
- **Label/Nav** (peso 600 `font-semibold`/`font-medium`, `text-sm`/`text-xs`, `tracking-wide`, uppercase quando é rótulo de status): navegação, rótulos de classificação, cabeçalhos de seção pequenos.
- **Body** (peso 400, `text-sm`/`text-base`): texto corrido, metodologia, descrições.

### Named Rules
**The Tabular Numerals Rule.** Todo número que representa um valor de indicador (não um índice de lista, não um ano) usa `tabular-nums` — números que mudam ao longo do tempo devem alinhar como colunas de uma tabela.

## Layout

Container central `max-w-6xl` com `px-4 sm:px-6`, mobile-first (o público primário — cidadão comum — acessa majoritariamente por celular). Grids usam `grid-cols-2 md:grid-cols-4` como padrão para blocos de estatística, com separadores internos por `border-l` em vez de gap+card. Header fixo (`sticky top-0`) com altura `h-16`, borda inferior de 1px em vez de sombra para se destacar do conteúdo.

Espaçamento vertical entre seções é generoso (`py-10` típico) para reforçar a leitura "uma seção = um bloco de jornal", não uma grade densa de widgets.

## Elevation & Depth

**Sistema inteiramente plano — zero sombra.** Não há `box-shadow` em nenhum componente. Profundidade e separação vêm exclusivamente de linhas de 1px (`border-ink` para divisões estruturais fortes, `border-gray-100` para divisões internas sutis) e de espaço em branco. Isso é uma decisão de marca, não uma lacuna: reforça a leitura de "documento/relatório oficial" sobre "produto de software".

### Named Rules
**The Flat-By-Default Rule.** Nenhum elemento recebe `box-shadow`, `backdrop-filter` ou glassmorphism. Se um elemento precisa se destacar, a ferramenta é borda ou peso tipográfico — nunca elevação.

## Shapes

**Cantos sempre retos.** Nenhum `border-radius` é usado em nenhum componente do sistema hoje — botões, badges, o selo do logotipo, cards — tudo com `rounded: 0`. Bordas são sempre finas (1px), nunca grossas ou decorativas.

### Named Rules
**The Square Corners Rule.** Não introduzir `rounded-*` em nenhum componente novo sem uma decisão explícita de rebrand — é a diferença mais visível entre "parece o IFB" e "parece um dashboard genérico de IA".

## Components

### Buttons
- **Shape:** reto, sem raio (0px).
- **Primary:** fundo `bg-yellow`, texto `text-ink`, `font-semibold`, `text-sm`, padding `px-4 py-2`. Usado só para a ação de apoio/doação — não para ações de navegação comuns.
- **Hover:** `hover:brightness-95` (o amarelo escurece levemente; nunca muda de matiz).
- **Link nav:** sem fundo, texto `text-gray-500` → `hover:text-ink`, transição de cor simples (`transition-colors`), sem sublinhado.

### Classification Badge (componente de assinatura)
Combinação obrigatória ícone geométrico + texto + cor semântica, nunca cor isolada: `▲ Melhorou` (verde), `▼ Piorou` (vermelho), `■ Estável` / `… Sem dados` (cinza neutro). Texto em `text-xs font-semibold uppercase tracking-wide`.

### Stat Blocks
- **Estrutura:** número grande (`.stat-figure`) sobre legenda pequena em `text-gray-500`, agrupados em grid com `border-t border-ink` no topo do bloco e `border-l border-gray-100` entre colunas — nunca card com fundo ou sombra.

### Navigation
- **Header:** fixo, fundo `paper`, borda inferior `border-ink`, logotipo quadrado tinta+amarelo ("IFB") + wordmark em duas linhas uppercase pequeno. Links em `text-gray-500`, ativo/hover em `text-ink`. Mobile usa um componente `MobileNav` dedicado (menu, não navegação horizontal comprimida).

## Do's and Don'ts

### Do:
- **Do** usar bordas finas de 1px (`border-ink` ou `border-gray-100`) para separar blocos — é o único mecanismo de divisão visual do sistema.
- **Do** parear toda classificação colorida (melhorou/piorou/estável) com um ícone geométrico e o rótulo por extenso.
- **Do** usar `tabular-nums` em qualquer número que representa um valor de indicador ao longo do tempo.
- **Do** manter o amarelo raro e intencional — CTA, logotipo, foco, destaque pontual.

### Don't:
- **Don't** adicionar `border-radius`, `box-shadow`, glassmorphism ou blur a qualquer componente — o sistema é plano e reto por design, não por lacuna de implementação.
- **Don't** usar o amarelo como fundo de uma seção inteira ou introduzir uma segunda cor de marca além dele.
- **Don't** trazer ícones de biblioteca (Lucide, Heroicons, Font Awesome) — o sistema usa apenas glifos Unicode simples (▲ ▼ ■ …) e o selo textual "IFB".
- **Don't** reverter o cinza secundário para `#737373` ou qualquer tom mais claro que `#656565` — foi escurecido deliberadamente para atingir WCAG AA.
