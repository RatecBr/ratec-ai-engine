# ADR 002 — Separação entre Workflow e Pipeline

**Status:** Aceito  
**Data:** 2026-06-29

## Contexto

Na versão inicial, Workflow e Pipeline eram o mesmo conceito.
Isso gerava acoplamento entre a lógica de negócio e os detalhes técnicos de execução.

## Decisão

Separar em dois conceitos distintos:

- **Workflow**: processo de negócio. Declara *o que* precisa ser feito.
  Seus steps referenciam apenas `pipeline_id`.

- **Pipeline**: orquestração técnica. Declara *como* fazer.
  Seus steps referenciam `capability`, `action`, `model_id` e `execution_strategy`.

## Consequências

**Positivo:**
- Um mesmo Pipeline pode ser reutilizado por múltiplos Workflows
- Workflows podem ser criados por stakeholders de negócio sem conhecimento técnico
- Mudança de modelo (FLUX → SDXL) não exige alteração em nenhum Workflow

**Negativo:**
- Duas entidades em vez de uma para conceitos simples
- Registro duplo (WorkflowRegistry + PipelineRegistry)
