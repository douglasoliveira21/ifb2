# Como colocar o IFB no ar usando o EasyPanel (tutorial para leigos)

Este tutorial assume que você **não tem experiência técnica** e vai te guiar
passo a passo, sem pular nada. No final, o site do Instituto Fiscaliza
Brasil vai estar publicado, com dados reais, em um endereço próprio.

O repositório do projeto é: `https://github.com/douglasoliveira21/ifb2`

---

## O que você vai criar

4 peças, todas dentro do mesmo Projeto no EasyPanel:

1. **Banco de dados** (PostgreSQL) — onde os dados ficam guardados
2. **Backend** — o "motor" que busca os dados oficiais e responde perguntas
3. **Frontend** — o site que as pessoas vão ver
4. **Sincronização automática** — busca dados novos todo dia, sozinha

---

## Pré-requisito: ter o EasyPanel instalado

Se você **já tem um servidor com EasyPanel rodando**, pule para a Parte 1.

Se você **ainda não tem**, precisa de um servidor (VPS) — pode ser da
Hetzner, DigitalOcean, Contabo, etc. Qualquer um com pelo menos **2 vCPU e
4 GB de RAM** (o projeto foi desenhado para caber nisso). Depois de criar o
servidor (Ubuntu 22.04 é uma boa escolha), acesse ele via SSH e rode:

```bash
curl -sSL https://get.easypanel.io | sh
```

Espere terminar, depois acesse `http://SEU_IP_DO_SERVIDOR:3000` no navegador
e crie sua conta de administrador do EasyPanel. Isso é uma instalação única
— depois disso você nunca mais precisa usar o terminal do servidor.

---

## Parte 1 — Criar o Projeto

1. Entre no painel do EasyPanel.
2. Clique em **"Create Project"** (ou o botão "+").
3. Dê um nome, por exemplo `ifb`.
4. Entre no projeto recém-criado. Você vai ver uma área vazia onde vamos
   adicionar os 4 serviços.

---

## Parte 2 — Criar o banco de dados (PostgreSQL)

1. Dentro do projeto `ifb`, clique em **"+ Service"** (ou "Create Service").
2. Escolha o tipo **"Database"** → **"PostgreSQL"**.
3. Configure:
   - **Nome do serviço**: `db`
   - **Usuário**: `ifb`
   - **Senha**: crie uma senha forte e **anote em algum lugar seguro** —
     você vai precisar dela daqui a pouco. Exemplo de senha forte:
     `Xk9$mQ2vLp7#nR4w` (não use exatamente essa, crie a sua).
   - **Nome do banco**: `ifb`
4. Clique em **"Create"** e espere o banco subir (fica com uma bolinha
   verde quando estiver pronto).

Anote o **nome interno** desse serviço (geralmente aparece como `db` ou
`ifb_db` — o EasyPanel mostra isso na tela do serviço). Você vai usar esse
nome para montar o endereço de conexão do backend.

---

## Parte 3 — Criar o Backend

1. No projeto, clique em **"+ Service"** → **"App"**.
2. Em **"Source"**, escolha **"GitHub"** (ou "Git") e cole o endereço do
   repositório: `https://github.com/douglasoliveira21/ifb2`
   - Se o repositório for privado, o EasyPanel vai pedir para autorizar
     acesso à sua conta do GitHub — siga as instruções na tela.
3. Em **"Build path"** ou **"Root directory"**, digite: `backend`
   (isso diz ao EasyPanel para usar a pasta `backend/` do repositório,
   onde está o `Dockerfile`).
4. Deixe o tipo de build como **"Dockerfile"** (o EasyPanel já vai detectar
   o `backend/Dockerfile` automaticamente).
5. Nome do serviço: `backend`.
6. Vá na aba **"Environment"** (variáveis de ambiente) e adicione,
   uma por linha:

   ```
   ENVIRONMENT=production
   DATABASE_URL=postgresql+psycopg://ifb:SUA_SENHA_DO_BANCO@db:5432/ifb
   CORS_ORIGINS=https://SEU-DOMINIO-DO-FRONTEND
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=crie-outra-senha-forte-aqui
   ```

   Troque:
   - `SUA_SENHA_DO_BANCO` pela senha que você criou na Parte 2
   - `db` pelo nome interno do serviço de banco (se for diferente)
   - `SEU-DOMINIO-DO-FRONTEND` pelo domínio que você vai usar no frontend
     (ex: `ifb.seudominio.com.br`) — se ainda não sabe, pode deixar
     `http://localhost:3000` por enquanto e ajustar depois
   - `ADMIN_PASSWORD` por uma senha forte e diferente da do banco — é a
     senha que você vai usar para entrar em `/admin`

7. Em **"Port"**, configure `8000` (é a porta que o backend usa por
   dentro do container).
8. Clique em **"Create"** / **"Deploy"**. O EasyPanel vai baixar o
   código, montar a imagem Docker e subir o serviço. Isso leva alguns
   minutos na primeira vez.
9. Quando terminar, vá em **"Domains"** dentro do serviço `backend` e
   ative um domínio (o EasyPanel pode gerar um `*.easypanel.host` grátis
   automaticamente, ou você aponta seu próprio domínio/subdomínio, ex:
   `api.seudominio.com.br`). **Anote essa URL** — vamos usar no frontend.

### Rodar as migrations (criar as tabelas no banco)

O `Dockerfile` do backend já roda `alembic upgrade head` automaticamente
toda vez que o serviço inicia — então, se o deploy terminou sem erro nos
logs, **as tabelas já foram criadas**. Para conferir:

1. Vá na aba **"Logs"** do serviço `backend`.
2. Procure por uma linha mencionando `alembic` ou `Running upgrade` — se
   não houver erro em vermelho, está tudo certo.

---

## Parte 4 — Criar o Frontend

1. No projeto, clique em **"+ Service"** → **"App"** de novo.
2. Fonte: o mesmo repositório GitHub.
3. **Build path** / **Root directory**: `frontend`
4. Nome do serviço: `frontend`.
5. Variáveis de ambiente:

   ```
   NEXT_PUBLIC_API_URL=https://URL_DO_BACKEND_QUE_VOCE_ANOTOU
   NEXT_PUBLIC_SITE_URL=https://SEU-DOMINIO-DO-FRONTEND
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=a-mesma-senha-que-voce-colocou-no-backend
   ```

   **Importante**: `ADMIN_USERNAME`/`ADMIN_PASSWORD` do frontend têm que
   ser **exatamente iguais** aos que você colocou no backend — é a mesma
   senha protegendo os dois lados de `/admin`.

6. **Port**: `3000`.
7. Clique em **"Create"** / **"Deploy"** e espere terminar.
8. Vá em **"Domains"** e ative o domínio final do site (ex:
   `ifb.seudominio.com.br` ou o domínio gratuito do EasyPanel). O
   EasyPanel cuida do certificado HTTPS automaticamente.
9. **Volte no serviço `backend`** e corrija a variável `CORS_ORIGINS` para
   o domínio real do frontend que você acabou de ativar (se você deixou
   um valor provisório antes). Depois de mudar, clique em **"Redeploy"**
   no backend.

Neste ponto, acessando o domínio do frontend você já deve ver o site — mas
ainda **sem indicadores** (o banco está vazio). Vamos resolver isso agora.

---

## Parte 5 — Buscar os dados reais pela primeira vez

1. Vá no serviço **`backend`** dentro do EasyPanel.
2. Procure a aba **"Console"** ou **"Terminal"** (ícone de terminal —
   permite rodar um comando dentro do container que já está no ar).
3. Rode este comando:

   ```bash
   python -m app.sync.run
   ```

4. Espere terminar (leva alguns segundos). Você vai ver mensagens tipo
   `[desemprego] ok — X ponto(s) processado(s).` para cada fonte.
5. Pronto — os dados reais (desemprego, IPCA, Selic, dívida pública,
   desmatamento etc., direto do Banco Central, IBGE e INPE) já estão no
   banco. Atualize a página do site: os números devem aparecer.

Se algum indicador der erro (ex: a fonte oficial estava fora do ar
naquele momento), os outros continuam funcionando normalmente — cada
fonte é independente. Você pode rodar o comando de novo mais tarde.

---

## Parte 6 — Deixar a sincronização automática (todo dia)

Isso evita que você tenha que entrar no terminal manualmente toda vez que
quiser dados atualizados.

1. No projeto, procure a opção **"Cron Jobs"** (pode estar nas
   configurações do projeto ou como um tipo de serviço "+ Service" →
   "Cron Job", dependendo da versão do EasyPanel).
2. Configure um novo Cron Job:
   - **Fonte**: mesmo repositório GitHub, **Build path**: `backend`
     (mesma imagem do backend)
   - **Comando**: `python -m app.sync.run`
   - **Agendamento (schedule)**: `0 4 * * *` (todo dia às 4h da manhã,
     fora do horário de pico)
   - **Variáveis de ambiente**: as mesmas do serviço `backend`
     (`DATABASE_URL`, `ENVIRONMENT=production`)
3. Salve. A partir de agora, os dados se atualizam sozinhos todo dia.

> Se a sua versão do EasyPanel não tiver "Cron Jobs" como opção visível,
> não tem problema: você pode rodar `python -m app.sync.run` manualmente
> pelo Console do backend sempre que quiser atualizar (Parte 5), ou me
> avisar para buscarmos uma alternativa.

---

## Parte 7 — Testar tudo

Abra o domínio do seu frontend e confira:

- [ ] A Home mostra o "Placar Brasil" com números reais (não aparece
      nenhum aviso amarelo de "DADOS DE DEMONSTRAÇÃO")
- [ ] `/indicadores` lista os indicadores com valores
- [ ] Clicar em um indicador mostra o gráfico histórico
- [ ] `/estados` e `/rankings` carregam
- [ ] `/transparencia` mostra as fontes e a data da última sincronização
- [ ] `/admin` pede usuário e senha (a que você configurou) — se pedir,
      está protegido corretamente
- [ ] Depois de logar em `/admin`, você consegue ver o painel

Se o aviso amarelo de "dados de demonstração" ainda aparecer, é sinal de
que o frontend não está conseguindo falar com o backend — confira se
`NEXT_PUBLIC_API_URL` no frontend está exatamente igual à URL pública do
backend (com `https://` e sem barra `/` no final).

---

## Resumo rápido (para quem já testou uma vez)

```
1. Criar projeto no EasyPanel
2. Serviço PostgreSQL → usuário ifb, senha forte, banco ifb
3. Serviço App "backend" (root: backend/) + variáveis de ambiente
4. Serviço App "frontend" (root: frontend/) + variáveis de ambiente
5. Console do backend → python -m app.sync.run
6. Cron Job diário → python -m app.sync.run
7. Testar o domínio do frontend
```

---

## Dúvidas comuns

**"Esqueci a senha do admin"** — edite a variável `ADMIN_PASSWORD` nos
dois serviços (backend e frontend) para uma nova senha e clique em
"Redeploy" nos dois.

**"Quero mudar o domínio"** — vá em "Domains" no serviço `frontend`,
adicione o novo domínio, e atualize `NEXT_PUBLIC_SITE_URL` e
`CORS_ORIGINS` (no backend) para o novo endereço.

**"O site está fora do ar"** — veja a aba "Logs" do serviço com problema
(backend ou frontend) — geralmente o erro aparece escrito em vermelho lá.
