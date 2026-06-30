# RATEC AI ENGINE — Diretrizes para o Assistente de IA

Este arquivo é carregado automaticamente em toda sessão. Seguir todas as regras abaixo sem exceção.

---

## Arquitetura (CONGELADA desde Epic 3)

- Não criar novas abstrações, padrões arquiteturais ou reorganizações de diretórios
- Não alterar responsabilidades do Engine (`src/`) ou do Runtime (`runtime/`)
- Não modificar a API pública
- Qualquer mudança estrutural exige ADR aprovada antes de implementação

## Antes de escrever qualquer código

1. **Reutilizar primeiro** — verificar se a funcionalidade já existe em: providers, workflows, capabilities, runtime
2. **Analisar como Capability** — perguntar: "pode ser reutilizada por outro produto RATEC?"
3. **Seguir o fluxo obrigatório**: Pesquisa → Modelos → Workflow → AI Playground → Benchmark → Validação → Capability → Publicação → Integração

## Capabilities

- Toda nova funcionalidade nasce como Capability reutilizável, nunca como código específico de produto
- Capabilities ficam em `runtime/models/catalog/` (manifest) e `workflows/image|audio|video|.../{id}/`
- Novo workflow = `comfyui.json` + `manifest.yaml` + entrada em `_CAPABILITY_ROUTES` no `runtime/__init__.py`
- Validar no AI Playground antes de qualquer integração com produto

## Os produtos nunca conhecem a IA

- Apps consomem apenas capabilities via API — nunca modelos, providers, workflows ou Runtime
- GOODLOOK é o primeiro consumidor, não o foco da plataforma
- Implementar sempre pensando nos 6 produtos: GOODLOOK, Audiover, Internice, Animapages, Karaokêro, Tradulino

## Infraestrutura

- Tudo via IaC: `scripts/start.sh`, `runtime/bootstrap.py`, variáveis de ambiente
- Modelos nunca na imagem Docker — sempre via Network Volume em `/runpod-volume/`
- Node "1" = LoadImage (convenção de todos os workflows ComfyUI)

## Antes de qualquer Sprint, Epic ou Release

Responder obrigatoriamente às 5 perguntas de valor:
1. Qual problema de negócio resolve?
2. Qual produto RATEC será beneficiado?
3. Pode ser reutilizada por outros produtos?
4. Existe Capability semelhante que pode ser evoluída?
5. Como medir o sucesso? (qualidade, tempo, custo, taxa de sucesso)

Se sem resposta clara → reavaliar antes de começar.

## AI Lab

- Todo resultado de execução deve ser registrado via `runtime/lab/` (quando no Playground)
- Cache experimental é opt-in — nunca automático em produção

## Política de modelos por Capability

Nenhuma Capability depende de um único modelo. Regras:
- Todo catálogo de modelo tem: `preferred`, `fallback_priority`, `requires_hf_token`, `license_type`
- O instalador (`scripts/install_models.py`) tenta modelos em prioridade; se um falha, tenta o próximo
- O Runtime lê `active_models.json` do Network Volume e seleciona o `comfyui.{model_id}.json` correto
- Novo modelo = manifest em `runtime/models/catalog/` + `comfyui.{model_id}.json` no workflow

## Dependências tecnológicas

Antes de adicionar qualquer nova dependência, responder:
- Já pode ser implementado com o Runtime existente?
- Existe modelo local equivalente?
- Reduz ou aumenta a complexidade?
- Será usada por vários produtos RATEC?
- Agrega valor real à plataforma?

Se resposta negativa → não incorporar.

**Firebase** permanece como backend principal (Auth, Firestore, Storage). Não migrar, não adicionar Supabase ou outro banco.  
**Geração de imagens** ocorre exclusivamente via AI Runtime (local). Nunca via API externa (Replicate, Stability, Fal.ai, etc.).  
**APIs externas permitidas** (apenas tarefas textuais): OpenAI, Claude, Gemini.  
**AI Runtime** nunca acessa Firestore diretamente — toda persistência passa pelo Engine.

## Referências rápidas

| O que fazer | Onde |
|-------------|------|
| Adicionar capability | `workflows/{cat}/{id}/` + `_CAPABILITY_ROUTES` |
| Adicionar modelo | `runtime/models/catalog/{id}/manifest.yaml` |
| Testar workflow | `uvicorn playground.server:app --port 7860` |
| Ver decisões | `docs/ratec-ai-engine-docs/DECISIONS.md` |
| Ver diretrizes | `docs/ratec-ai-engine-docs/DIRECTIVES.md` |
| Ver roadmap | `docs/ratec-ai-engine-docs/ROADMAP.md` |
