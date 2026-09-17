# Matinê

Plataforma pessoal e social para descobrir, organizar e escolher filmes.

## Estado atual

Bootstrap mínimo para o primeiro deploy na Vercel:

- Next.js 16
- React 19
- TypeScript strict
- headers básicos de segurança
- `/api/health` para health check
- nenhuma credencial ou dado sensível versionado

O backend FastAPI, Supabase e integração TMDB serão adicionados incrementalmente após o deploy base estar validado.

## Desenvolvimento local

```bash
npm install
npm run dev
```

Abra `http://localhost:3000`.

Health check:

```bash
curl http://localhost:3000/api/health
```

Resposta esperada:

```json
{"status":"ok","service":"matine-web"}
```

## Variáveis de ambiente

Copie `.env.example` para `.env.local` e preencha apenas localmente.

Nunca versione `.env`, `.env.local`, tokens ou chaves privadas.

Variáveis com prefixo `NEXT_PUBLIC_` podem ser expostas ao navegador. Segredos como `DATABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `TMDB_API_KEY` e `CRON_SECRET` devem permanecer exclusivamente server-side.

## Deploy

Importe o repositório `blasther12/matine` na Vercel usando a branch `main` e o preset Next.js.

Não adicione variáveis de ambiente até as integrações que dependem delas existirem no código.

Após o primeiro deploy, valide `/` e `/api/health`.
