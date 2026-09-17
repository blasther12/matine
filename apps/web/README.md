# Matinê Web

Frontend das Fases 0 e 1, construído com Next.js App Router, TypeScript, Tailwind CSS,
TanStack Query e Zod.

## Requisitos

- Node.js 20.9 ou superior
- pnpm 11

## Comandos

Execute a partir da raiz do monorepo:

```bash
pnpm install
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

Também é possível executar os scripts diretamente neste diretório.

## Segurança

- `src/proxy.ts` gera um nonce imprevisível por requisição e envia uma CSP restritiva.
- A página chama `connection()` porque CSP com nonce exige renderização dinâmica no Next.js.
- O build de produção usa Webpack temporariamente. O Proxy do Next.js 16.3/Turbopack possui uma regressão confirmada no `next start` para Windows; o build Webpack mantém o mesmo código e responde corretamente nesse ambiente.
- `next.config.ts` remove o header de tecnologia e adiciona headers de isolamento, privacidade e prevenção de MIME sniffing/framing.
- HSTS é enviado somente em produção, para não interferir no desenvolvimento local.
- O browser consulta somente `/api/backend`, no mesmo domínio. Com `API_INTERNAL_URL`, o Next.js encaminha para a FastAPI; sem essa variável, um Route Handler server-side consulta o TMDB.
- `TMDB_API_KEY` é exclusivamente server-side em ambos os modos e nunca deve receber o prefixo `NEXT_PUBLIC_`.
- Imagens aceitam somente o host e o path fixos do TMDB; trailer é link externo, nunca embed arbitrário.
- Não há analytics, cookies, armazenamento local ou coleta de dados pessoais nesta fase.

## Escopo

`/search` oferece busca com debounce e `/movie/{tmdb_id}` mostra detalhes, créditos e
provedores BR. Autenticação e qualquer dado pessoal permanecem fora do escopo.

## Deploy independente na Vercel

Quando apenas `apps/web` é implantado, cadastre `TMDB_API_KEY` como variável sensível
nos ambientes Production e Preview. `TMDB_BASE_URL`, `TMDB_LANGUAGE` e `TMDB_REGION`
são opcionais; os padrões são a API oficial do TMDB, `pt-BR` e `BR`.

Se uma FastAPI externa estiver disponível, configure `API_INTERNAL_URL` com sua origem
HTTPS. Essa variável substitui o Route Handler interno sem expor a origem ao browser.
