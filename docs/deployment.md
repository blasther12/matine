# Versionamento e entrega

## Fluxos

| Workflow | Disparo | Resultado |
| --- | --- | --- |
| `PR title` | abertura ou edição de pull request | exige título em Conventional Commits |
| `Release` | push em `main` ou execução manual | mantém o release PR, cria tag e GitHub Release |
| `Publish container images` | chamado pelo release ou manualmente | publica API e web no GHCR |

Os workflows de publicação não recebem segredos da aplicação. O token automático
do GitHub é usado apenas com permissões explícitas e limitadas ao job.

## Versionamento

O Release Please interpreta os commits convencionais:

- `fix:` gera patch;
- `feat:` gera minor;
- `feat!:` ou `BREAKING CHANGE:` gera mudança incompatível;
- enquanto a versão for menor que 1.0, mudanças incompatíveis incrementam minor.

O release PR atualiza `CHANGELOG.md`, `package.json`,
`apps/web/package.json`, `apps/api/pyproject.toml` e o manifesto de versão.
Ao mesclar esse PR, o workflow cria uma tag `vX.Y.Z` e um GitHub Release.

## Imagens

Cada release publica imagens multi-arquitetura para Linux AMD64 e ARM64:

- `ghcr.io/<owner>/<repo>-api:<tag>`;
- `ghcr.io/<owner>/<repo>-web:<tag>`.

As imagens recebem a versão do release, `latest` e uma tag imutável baseada no
SHA. BuildKit adiciona SBOM e proveniência. A atestação GitHub adicional roda
somente para repositórios públicos, porque planos pessoais não oferecem esse
recurso para repositórios privados.

Use versões imutáveis em produção, nunca apenas `latest`. Segredos como
`DATABASE_URL` e `TMDB_API_KEY` devem vir do secret manager do ambiente de
execução; não são argumentos de build nem valores do workflow.

## Configuração inicial no GitHub

1. Em **Settings > Actions > General**, permita que Actions criem pull requests,
   ou configure `RELEASE_PLEASE_TOKEN` como token fine-grained com o menor
   acesso necessário a contents, issues e pull requests.
2. Proteja `main` exigindo os checks de CI e `PR title`.
3. Confirme que o pacote GHCR herda o acesso correto do repositório.

Com o `GITHUB_TOKEN`, eventos criados pelo release PR podem não iniciar outros
workflows. Se a proteção da branch exigir CI no release PR, use
`RELEASE_PLEASE_TOKEN`; nunca use um token pessoal amplo.

## Execução manual

O workflow `Publish container images` aceita um ref, uma tag OCI e a opção de
atualizar `latest`. Isso permite republicar um release ou criar uma imagem
`edge` sem fabricar uma nova versão.

Este pipeline termina no GHCR. O deploy em Render, Fly.io, Kubernetes, AWS ou
outro runtime deve consumir essas imagens por digest e executar as migrações
Alembic como etapa única antes de promover a API.
