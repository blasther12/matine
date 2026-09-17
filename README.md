# Matinê

Plataforma cinematográfica pessoal e social, construída de forma incremental
com privacidade por padrão. A primeira entrega implementa a fundação técnica e
o catálogo público TMDB; contas, biblioteca pessoal e dados sociais continuam
deliberadamente fora do escopo até a base de autorização da Fase 2.

## Estado atual

- **Fase 0 — Foundation:** monorepo, FastAPI, Next.js, PostgreSQL, Alembic,
  Docker, testes, CI e baseline de segurança.
- **Fase 1 — TMDB:** busca, detalhes, créditos e disponibilidade no Brasil,
  com cache apenas de metadados públicos.
- **Próxima fase recomendada:** Supabase Auth, `/me`, autorização no backend e
  RLS deny-by-default antes de armazenar qualquer atividade pessoal.

## Arquitetura

```text
Browser -> Next.js -> FastAPI -> TMDB
                         |
                         +----> PostgreSQL (cache público)
```

O código é um monólito modular:

```text
apps/web        Next.js App Router + TypeScript + Tailwind
apps/api        FastAPI + SQLAlchemy 2 + Alembic
packages/shared contratos gerados, quando houver duplicação real
docs            arquitetura, segurança, dados, API e threat model
```

O navegador nunca recebe o token TMDB, credenciais do banco ou a futura chave
Supabase Service Role. A API retorna schemas explícitos; payloads brutos do TMDB
e objetos ORM não atravessam a fronteira pública.

## Pré-requisitos

- Python 3.12+
- Node.js 20.9+
- pnpm 11
- Docker com Compose, ou PostgreSQL local dedicado
- TMDB API Read Access Token para usar as rotas de catálogo

## Configuração

Copie o arquivo de exemplo sem versionar o resultado:

```powershell
Copy-Item .env.example .env
```

Preencha `TMDB_API_KEY` com o **API Read Access Token** do TMDB. Apesar do nome
histórico da variável, o valor é enviado somente como `Authorization: Bearer`
e nunca como query string. Não coloque esse valor em nenhuma variável
`NEXT_PUBLIC_*`.

## Executar com Docker

```powershell
docker compose config
docker compose up --build
```

- Web: `http://localhost:3000`
- API: `http://localhost:8000`
- Health: `http://localhost:8000/health`

O PostgreSQL de desenvolvimento é publicado somente em `127.0.0.1`. Se já
houver um serviço usando a porta 5432, ajuste-a em um override local.

## Desenvolvimento nativo

Backend, a partir de `apps/api`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -c requirements.lock -e ".[dev]"
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Frontend, a partir da raiz:

```powershell
pnpm install --frozen-lockfile
pnpm dev
```

## Verificação

Backend:

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy app
python -m bandit -q -r app
python -m pip_audit
```

Frontend:

```powershell
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm audit --audit-level high
```

Os testes de catálogo usam mocks HTTP e não precisam de token real nem fazem
chamadas ao TMDB. Consulte [docs/development.md](docs/development.md) para o
fluxo offline e a separação de banco de testes.

## Endpoints disponíveis

```text
GET /health
GET /movies/search?q=&page=
GET /movies/{tmdb_id}
GET /movies/{tmdb_id}/credits
GET /movies/{tmdb_id}/providers
```

As rotas TMDB têm entrada limitada, erros sanitizados e rate limit local. Busca
não é persistida nem registrada. Detalhes têm TTL de 24 horas, créditos de 7
dias e provedores BR de 6 horas.

## Telas disponíveis

- `/` — apresentação do produto e princípios de privacidade.
- `/search` — busca de filmes com debounce e estados de loading/erro/vazio.
- `/movie/{tmdb_id}` — detalhes, direção, elenco, trailer e provedores BR.

## Banco de dados

Nesta entrega existe somente `external_cache`, usado para respostas públicas e
normalizadas do TMDB. Não há tabelas de usuário, autenticação, histórico,
avaliações ou perfil. Termos de busca nunca entram no cache.

## Decisões de segurança e privacidade

- configuração de produção falha com CORS/hosts inseguros;
- logs estruturados omitem query, IP, corpos, cookies e headers de autorização;
- CSP, proteção contra framing, `nosniff`, política de referrer e HSTS em
  produção;
- nenhuma analytics, publicidade, fingerprinting ou cookie de terceiros;
- rate limit em memória é efêmero e não cria histórico de IP;
- respostas de erro não expõem stack, SQL, paths, configuração ou upstream;
- CI usa `permissions: contents: read` e executa testes e auditorias.

Mais detalhes em [SECURITY.md](SECURITY.md),
[docs/data-map.md](docs/data-map.md) e
[docs/threat-model.md](docs/threat-model.md). O contrato público e a integração
externa estão em [docs/api.md](docs/api.md) e [docs/tmdb.md](docs/tmdb.md).

## Limitações conhecidas

- O rate limiter é por processo; uma implantação horizontal deverá aplicar
  limite também na borda antes de depender de uma cota global.
- A disponibilidade é a informação reportada pelo TMDB/JustWatch para `BR` e
  pode não refletir mudanças instantaneamente.
- A primeira instalação e as auditorias atualizadas dependem de rede.
- Autenticação, biblioteca pessoal, diário, reviews e social ainda não existem;
  isso evita coletar dados antes da política de autorização e RLS.
- O build web usa Webpack no Windows enquanto uma regressão do Proxy com
  Turbopack no Next.js 16 permanecer relevante.

Este produto usa a API do TMDB, mas não é endossado nem certificado pelo TMDB.
Dados de disponibilidade exigem atribuição ao JustWatch.
