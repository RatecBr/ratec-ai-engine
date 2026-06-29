# ADR 001 — Clean Architecture como base do projeto

**Status:** Aceito  
**Data:** 2026-06-29

## Contexto

O RATEC AI ENGINE deve servir múltiplos produtos durante muitos anos sem que mudanças
de infraestrutura (trocar RunPod, atualizar modelos) impactem os consumidores.

## Decisão

Adotar Clean Architecture com 4 camadas explícitas:

1. **Domain** — entidades e interfaces puras (zero dependências externas)
2. **Application** — use cases que orquestram o domínio
3. **Infrastructure** — implementações concretas (FastAPI, RunPod, registries)
4. **API** — roteamento HTTP (apresentação)

A regra de dependência flui para dentro: Infrastructure → Application → Domain.

## Consequências

**Positivo:**
- Trocar qualquer provider/backend não quebra use cases nem o domínio
- Testabilidade: use cases testáveis com mocks das interfaces
- Clareza: cada arquivo tem um único motivo para mudar

**Negativo:**
- Mais arquivos e boilerplate inicial
- Curva de aprendizado para novos desenvolvedores

## Alternativas consideradas

- **FastAPI + SQLAlchemy direto**: mais simples inicialmente, mas acopla regras de negócio à infraestrutura
- **Django**: overhead desnecessário para uma plataforma de AI jobs
