# Estratégia de Branches — RATEC AI ENGINE

## Estrutura

```
main        ← produção (estável)
develop     ← integração de desenvolvimento
feature/*   ← funcionalidades novas
hotfix/*    ← correções urgentes em produção
```

## Regras obrigatórias

### main
- **Nunca** recebe push direto (`git push origin main` é proibido)
- Só recebe merge vindo de `develop` via Pull Request
- Cada merge em `main` representa uma versão pronta para produção
- O PR deve ter ao menos uma revisão antes de ser mergeado

### develop
- Branch de trabalho principal do dia a dia
- Recebe merges de `feature/*` e `hotfix/*`
- Pode receber commits diretos para ajustes pequenos

### feature/*
- Criada a partir de `develop`
- Nomenclatura: `feature/nome-da-funcionalidade`
- Mergeada de volta em `develop` via PR ao concluir

```bash
git checkout develop
git checkout -b feature/goodlook-integration
# ... trabalho ...
git push origin feature/goodlook-integration
# abrir PR → develop
```

### hotfix/*
- Criada a partir de `main` para corrigir bugs críticos em produção
- Mergeada em `main` E em `develop` após a correção

```bash
git checkout main
git checkout -b hotfix/descricao-do-bug
# ... correção ...
# PR → main  +  PR → develop
```

## Fluxo normal de desenvolvimento

```
feature/xyz  →  develop  →  (quando pronto)  →  main
```

1. Criar branch a partir de `develop`
2. Desenvolver e commitar
3. Abrir PR de `feature/xyz` → `develop`
4. Revisar, aprovar e mergear
5. Quando `develop` estiver estável e testado → PR de `develop` → `main`

## Convenção de commits

Seguir o padrão **Conventional Commits**:

```
feat: nova funcionalidade
fix: correção de bug
refactor: refatoração sem mudança de comportamento
docs: documentação
test: testes
chore: tarefas de manutenção (deps, config)
```

## Branch padrão para novos trabalhos

Sempre iniciar a partir de `develop`:

```bash
git checkout develop
git pull origin develop
git checkout -b feature/minha-feature
```
