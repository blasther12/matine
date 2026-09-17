# Contribuindo com a Matinê

Obrigado por ajudar a construir uma experiência de cinema mais privada e
confiável.

## Antes de começar

1. Leia o [threat model](docs/threat-model.md) e o
   [mapa de dados](docs/data-map.md).
2. Para mudanças de produto, declare os dados necessários, visibilidade,
   retenção, autorização e risco de troca de identificadores.
3. Nunca inclua tokens, arquivos `.env`, dados reais de usuários ou payloads
   sensíveis em código, fixtures, issues ou logs.

Vulnerabilidades não devem ser reportadas em issues públicas. Use o processo
descrito em [SECURITY.md](SECURITY.md).

## Ambiente

```bash
git clone git@github.com:blasther12/matine.git
cd matine
cp .env.example .env
pnpm install --frozen-lockfile

cd apps/api
python3 -m venv .venv
.venv/bin/python -m pip install -c requirements.lock -e ".[dev]"
```

O token TMDB não é necessário para os testes: a integração externa usa mocks.

## Fluxo de trabalho

1. Crie uma branch pequena e focada.
2. Implemente testes proporcionais ao risco.
3. Execute as verificações descritas no README.
4. Abra um pull request usando o template do projeto.

Use Conventional Commits no título do PR:

```text
feat(search): add genre filters
fix(api): bound upstream response size
docs(security): clarify retention policy
```

- `feat` cria uma versão minor;
- `fix` cria uma versão patch;
- `feat!` ou `BREAKING CHANGE` sinaliza incompatibilidade.

## Checklist de segurança

- O endpoint valida entrada, autenticação e propriedade?
- Trocar um ID permite acessar dados de outra pessoa?
- Logs e erros continuam sem segredos ou dados pessoais?
- O campo novo é realmente necessário?
- Existe uma política explícita de retenção?
- Migrações preservam deny-by-default e podem ser revertidas com segurança?
- Dependências, imagens e Actions vêm de fontes confiáveis?

Mudanças que envolvam autenticação, cookies, uploads, dados de usuário,
visibilidade social, RLS ou novos terceiros devem atualizar a documentação de
segurança antes do merge.
