# DIRETRIZES PERMANENTES DE DESENVOLVIMENTO

**Vigência:** a partir da Release v1.0.0-alpha  
**Escopo:** toda implementação realizada no RATEC AI ENGINE

Estas diretrizes fazem parte da arquitetura oficial da plataforma e têm precedência sobre qualquer convenção anterior.

---

## 1. Reutilização antes de Implementação

Antes de escrever qualquer linha de código, analisar toda a plataforma para verificar se a funcionalidade solicitada já existe.

Sempre priorizar:

- reutilização de código
- reutilização de Providers
- reutilização de Workflows
- reutilização de Capabilities
- reutilização de componentes do Runtime

Nunca implementar uma funcionalidade que já possa ser obtida reutilizando componentes existentes.

---

## 2. Pensar em Capabilities, não em Aplicações

Toda nova solicitação deve ser analisada como uma possível Capability reutilizável.

Evitar implementar funcionalidades específicas para qualquer produto (GOODLOOK, Audiover, Internice, Animapages, Karaokêro, Tradulino).

Sempre perguntar antes de implementar:

> "Essa funcionalidade pode ser reutilizada por outro produto da RATEC?"

Se a resposta for sim, ela deve nascer como uma Capability da plataforma.

---

## 3. Arquitetura Congelada

A arquitetura principal permanece estável desde o Epic 3.

Evitar:

- novas abstrações
- novos padrões arquiteturais
- reorganizações de diretórios
- mudanças de responsabilidades entre Engine e Runtime
- alterações na API pública

Mudanças arquiteturais somente mediante ADR aprovada e documentada em `docs/ratec-ai-engine-docs/DECISIONS.md`.

---

## 4. Todo Desenvolvimento Começa pelo AI Playground

Nenhuma nova Capability é implementada diretamente para um aplicativo.

Fluxo obrigatório:

```
Pesquisa
  ↓
Modelos (manifest em runtime/models/catalog/)
  ↓
Workflow (comfyui.json + manifest.yaml em workflows/)
  ↓
AI Playground (uvicorn playground.server:app --port 7860)
  ↓
Benchmark (métricas registradas no AI Lab)
  ↓
Validação (avaliação manual, score mínimo definido)
  ↓
Capability (publicada via _CAPABILITY_ROUTES)
  ↓
Integração com Produtos (via API pública)
```

---

## 5. Os Produtos Nunca Conhecem a IA

Os aplicativos consumidores jamais conhecem:

- modelos
- Providers
- Workflows
- ComfyUI
- Runtime
- detalhes internos da plataforma

Os aplicativos consomem apenas Capabilities publicadas através da API oficial.

---

## 6. Toda Implementação Deve Ser Reproduzível

Toda infraestrutura segue Infrastructure as Code.

Nunca depender de configurações manuais.

Toda instalação deve ser possível apenas:

1. clonando o repositório
2. configurando variáveis de ambiente (`.env`)
3. executando scripts de bootstrap (`scripts/start.sh`, `runtime/bootstrap.py`)

---

## 7. Pensar como Plataforma

Antes de implementar qualquer funcionalidade, responder:

- Essa funcionalidade poderá ser reutilizada?
- Ela pertence ao Engine ou ao Runtime?
- Ela deve ser uma Capability?
- Ela poderá servir outros produtos?
- Ela está seguindo a arquitetura existente?
- Existe alguma implementação semelhante que possa ser reutilizada?

---

## 8. Como Solicitar Novas Funcionalidades

Evitar solicitações genéricas como "Implemente Haircut" ou "Implemente OCR".

**Formato correto:**

> "Crie uma nova Capability chamada `{nome}`, seguindo o ciclo de vida completo da plataforma (pesquisa → workflow → benchmark → validação → publicação), utilizando exclusivamente a arquitetura existente, reutilizando componentes já implementados, registrando a Capability no catálogo, associando os modelos necessários, documentando os requisitos e disponibilizando-a para consumo apenas quando atingir o estado PUBLISHED."

---

## 9. A Plataforma Sempre Vem Antes do Produto

Em caso de dúvida entre criar uma solução específica para um aplicativo ou criar uma Capability reutilizável:

**A prioridade é sempre a plataforma.**

Os aplicativos adaptam-se à plataforma. A plataforma nunca é adaptada para atender um único aplicativo.

---

## 10. Missão do RATEC AI ENGINE

O RATEC AI ENGINE não é um projeto voltado ao GOODLOOK.

O GOODLOOK é apenas o primeiro consumidor da plataforma.

**Missão oficial:**

> Fornecer uma infraestrutura centralizada de Inteligência Artificial capaz de atender qualquer produto da RATEC por meio de Capabilities reutilizáveis, desacopladas e continuamente evoluídas.

Toda decisão futura deve preservar essa missão.

---

## 11. Evolução Orientada por Valor

Antes de iniciar qualquer nova Sprint, Epic ou Release, responder obrigatoriamente:

- Qual problema de negócio esta implementação resolve?
- Qual produto da RATEC será beneficiado?
- Essa funcionalidade poderá ser reutilizada por outros produtos?
- Existe alguma Capability semelhante que possa ser evoluída em vez de criar uma nova?
- Como será medido o sucesso dessa Capability (qualidade, tempo, custo, taxa de sucesso etc.)?

Se essas perguntas não tiverem respostas claras, a implementação deve ser reavaliada antes de começar.

---

## Referência de implementação

| Ação | Como fazer |
|------|-----------|
| Nova Capability | `workflows/{cat}/{id}/comfyui.json` + `manifest.yaml` + entrada em `_CAPABILITY_ROUTES` |
| Novo modelo | `runtime/models/catalog/{id}/manifest.yaml` |
| Testar localmente | `uvicorn playground.server:app --port 7860` |
| Registrar benchmark | Automático via AI Lab ao executar no Playground |
| Documentar decisão | `docs/ratec-ai-engine-docs/DECISIONS.md` |
