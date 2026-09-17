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
- O browser consulta a API pelo proxy same-origin `/api/backend`; o token TMDB permanece no FastAPI.
- Imagens aceitam somente o host e o path fixos do TMDB; trailer é link externo, nunca embed arbitrário.
- Não há analytics, cookies, armazenamento local ou coleta de dados pessoais nesta fase.

## Escopo

`/search` oferece busca com debounce e `/movie/{tmdb_id}` mostra detalhes, créditos e
provedores BR. Autenticação e qualquer dado pessoal permanecem fora do escopo.
