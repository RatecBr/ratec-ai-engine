# Decisões Arquiteturais

## Clean Architecture

**Decisão:** Adotar Clean Architecture com 4 camadas: Domain → Application → Infrastructure → API.

**Motivo:** Isolar regras de negócio de infraestrutura (RunPod, ComfyUI, modelos). Permite trocar providers e backends sem tocar em lógica de domínio.

**Consequências:** Inversão de dependência obrigatória; camadas superiores dependem de interfaces.

---

## API First

**Decisão:** Documentar o contrato da API antes de implementar.

**Motivo:** Múltiplos produtos da RATEC consomem a mesma API. O contrato público é a interface de integração.

---

## RunPod Serverless

**Decisão:** Usar RunPod Serverless como infraestrutura de compute GPU.

**Motivo:** Pay-per-use, scale-to-zero, sem gerenciamento de servidores. Adequado para workloads de IA com demanda variável.

---

## GPU restrita a AMPERE_48 (RTX A5000 24GB)

**Decisão:** Endpoint RunPod configurado com `gpuIds: AMPERE_48` exclusivamente.

**Motivo:** Workflows de imagem com ComfyUI requerem mínimo de 24GB VRAM. Misturar GPUs menores causaria falhas silenciosas ou degradação de qualidade. Hardware correto é pré-condição, não otimização.

**Como foi feito:** Mutation GraphQL `saveEndpoint` com `gpuIds: ["AMPERE_48"]`.

**Código é GPU-agnostic:** A aplicação nunca verifica qual GPU está rodando. A política de hardware é responsabilidade da infraestrutura (RunPod config), não do código.

---

## ComfyUI como Provider

**Decisão:** ComfyUI é integrado como um `Provider` desacoplado seguindo os padrões do sistema.

**Motivo:** Permite substituir ou adicionar outros providers (Stable Diffusion Web UI, A1111, etc.) sem alterar a lógica de execução. O `ExecutionManager` roteia para o backend correto via `execution_strategy`.

**Implementação:** `src/infrastructure/providers/comfyui/` com 8 arquivos; `ComfyUIBackend` registrado no `ExecutionManager`.

---

## Modelos fora da imagem Docker (Network Volume)

**Decisão:** Nenhum modelo de IA é incluído na imagem Docker. Todos os modelos são carregados via RunPod Network Volume.

**Motivo:** Imagens Docker com modelos chegam a dezenas de GB, tornando o build e pull lentos. Network Volume persiste entre execuções e pode ser atualizado independentemente do código.

**Como funciona:** `start.sh` cria symlinks de `/comfyui/models/` → `/runpod-volume/models/` no boot.

---

## Módulo `runtime/` standalone

**Decisão:** Toda a lógica do handler RunPod vive em `runtime/`, um pacote Python sem dependências de `src/`.

**Motivo:** O handler RunPod (`handler.py`) não pode importar de `src/` porque o PYTHONPATH no container não inclui a estrutura de projeto completa. Manter tudo em `runtime/` evita problemas de importação e mantém o handler testável de forma isolada.

**Consequência:** Existe alguma duplicação de conceitos entre `runtime/` e `src/infrastructure/providers/comfyui/`. Esta duplicação é intencional — o `runtime/` é uma implementação de produção minimalista e autossuficiente.

---

## IaC via `scripts/start.sh` e `runtime/bootstrap.py`

**Decisão:** Todo o setup do ambiente (dirs, symlinks, validações) é feito via código no boot, nunca manualmente no painel do RunPod.

**Motivo:** Configurações manuais são frágeis, não versionadas e impossíveis de auditar. Tudo que o container precisa para funcionar deve ser declarado em código.

---

## Workflows por categoria

**Decisão:** Workflows organizados em categorias: `workflows/image/`, `workflows/audio/`, `workflows/video/`, `workflows/vision/`, `workflows/multimodal/`.

**Motivo:** Escalabilidade. A plataforma atende 6 produtos RATEC com capacidades distintas. A organização por categoria facilita descoberta e evita conflitos de nomes.

---

## Congelamento da arquitetura (Epic 3)

**Decisão:** A partir do Epic 3, nenhuma reorganização estrutural, alteração de responsabilidades do Engine/Runtime, modificação da API pública ou criação de novos padrões arquiteturais sem uma ADR (Architecture Decision Record) aprovada.

**Motivo:** A plataforma atingiu maturidade arquitetural. A prioridade agora é a evolução de capabilities, não de infraestrutura. Mudanças estruturais interrompem o trabalho de validação de modelos e atrasam a entrega de valor.

**Como aplicar:** Qualquer proposta de mudança estrutural deve ser documentada como ADR com alternativas analisadas antes de implementação. Novas funcionalidades usam exclusivamente a arquitetura existente.

---

## AI Lab como camada observacional (não invasiva)

**Decisão:** O AI Lab (`runtime/lab/`) é uma extensão observacional do Runtime — não modifica nenhum comportamento existente do Engine, Runtime ou handler RunPod.

**Motivo:** O handler de produção no RunPod não deve ter dependências do Lab (SQLite, arquivos, etc.). O Lab existe apenas no contexto do Playground local de desenvolvimento.

**Como funciona:** O Playground inicializa `Lab` separadamente. O Runtime não sabe que o Lab existe. O `record()` é chamado apenas no `playground/server.py`, nunca no `runtime/__init__.py`.

---

## Catálogo de modelos em manifests YAML (não em código)

**Decisão:** Cada modelo tem um manifest YAML em `runtime/models/catalog/{model}/manifest.yaml`. O catálogo não é um registro em código Python.

**Motivo:** Manifests são legíveis por humanos, versionados em git, e podem ser atualizados sem modificar código. Engenheiros e pesquisadores podem adicionar modelos sem tocar no Runtime.

**Campos obrigatórios:** id, name, version, vendor, license, category, status, installation.path, requirements.min_vram, capabilities.

---

## Cache experimental opt-in

**Decisão:** O cache experimental do AI Lab é ativado explicitamente pelo usuário no Playground, nunca automático.

**Motivo:** Resultados de IA não são determinísticos — o mesmo input pode produzir outputs diferentes dependendo de seed e temperatura. O cache é útil durante desenvolvimento/pesquisa, perigoso em produção.

**Chave de cache:** SHA-256 de `(workflow_id + input_image_hash + node_overrides)`. Qualquer diferença nos parâmetros invalida o cache.

---

## HairFastGAN descartado

**Decisão:** NÃO usar HairFastGAN como componente da plataforma.

**Motivo:** Resolve apenas um caso específico (alteração de cabelo), possui arquitetura própria, baixa reutilização entre produtos, dificulta padronização e cria dependência de uma solução específica.

**Alternativa:** FLUX + IPAdapter + segmentação de região + máscaras — mesmos componentes reutilizáveis pelos workflows haircut, beard, makeup e virtual-try-on.

---

## Executor genérico ComfyUI (sem código por workflow)

**Decisão:** O Runtime não tem handlers específicos por workflow. Um único executor genérico `_execute_comfyui()` serve todos os workflows ComfyUI.

**Motivo:** Adicionar código para cada novo workflow não escala. Um executor genérico + convenção (node "1" = LoadImage) permite adicionar workflows apenas com arquivos (`comfyui.json` + `manifest.yaml`), sem tocar no Runtime.

**Convenção:** Node "1" é sempre o input principal (LoadImage). O executor automaticamente faz upload da imagem e aplica ao node "1".

---

## Capability routing (apps não conhecem workflows)

**Decisão:** Apps solicitam capabilities (`background-remove`, `haircut`). O Runtime resolve internamente qual workflow usar via `_CAPABILITY_ROUTES`.

**Motivo:** Desacopla aplicativos da implementação técnica. Quando `haircut-v2` substituir `haircut-v1`, nenhum aplicativo precisa ser atualizado. O Engine decide.

---

## AI Playground obrigatório antes de integração

**Decisão:** Nenhum workflow é disponibilizado na API sem antes ser validado no AI Playground.

**Motivo:** Previne integração de workflows com bugs. O playground (`playground/`) permite testar visualmente sem precisar de aplicativo consumidor.

**Fluxo:** `Workflow → Playground → Capability → API → Aplicativo`

---

## Firebase como backend principal (Release 1.0.1-alpha)

**Decisão:** Firebase permanece como backend principal da plataforma. Nenhuma migração para outro serviço nesta fase.

**Componentes utilizados:**
- Firebase Authentication — autenticação de usuários e produtos
- Firestore — dados estruturados: usuários, aplicações, capabilities, histórico, benchmark, configurações, logs funcionais
- Firebase Storage — imagens enviadas, imagens processadas, datasets, arquivos temporários e resultados

**Motivo:** Infraestrutura já existente, madura e utilizada pelos produtos RATEC. Evitar nova dependência sem necessidade comprovada.

**Restrições:**
- Nenhum modelo é executado no Firebase
- Todo processamento pesado ocorre no RunPod
- O AI Runtime nunca acessa o Firestore diretamente
- Toda comunicação com Firebase ocorre através do RATEC AI ENGINE (Engine é o único responsável pela persistência)

---

## Modelos locais como estratégia padrão

**Decisão:** Toda geração de imagens ocorre localmente via AI Runtime. APIs externas de geração de imagens (Replicate, Stability API, Segmind, Fal.ai, Together AI, HuggingFace Inference API) não são utilizadas.

**APIs externas permitidas:** apenas para tarefas textuais e multimodais onde não há alternativa local estável:
- OpenAI — interpretação, geração de prompts, classificação, OCR inteligente, resumo
- Claude — raciocínio complexo, análise de documentos, revisão de conteúdo
- Gemini — interpretação multimodal, análise de imagens, tarefas de grande contexto

**Motivo:** Redução de custos, maior controle, independência tecnológica, facilidade de customização. Modelos locais são a estratégia de longo prazo da plataforma.

**Critério para incorporar nova API:** a API deve agregar valor que não pode ser obtido localmente, ser utilizada por múltiplos produtos RATEC e reduzir a complexidade geral.

---

## Modelos prioritários da plataforma (Release 1.0.1-alpha)

**Decisão:** Os modelos oficiais da plataforma são: BRIA RMBG, RealESRGAN, FLUX, ControlNet, IPAdapter, Whisper, PaddleOCR. Todos armazenados no Network Volume, nunca na imagem Docker.

**Motivo:** Definição clara do escopo de modelos para evitar proliferação descontrolada. Novos modelos devem ser avaliados antes de incorporados.

**Instalação:** via `scripts/install_models.py` (Model Installation Manager). Executado uma vez para popular o Network Volume.

---

## WorkflowValidator obrigatório

**Decisão:** Todo workflow deve passar pelo `WorkflowValidator` antes de ser registrado ou executado.

**Motivo:** Falhas em workflows ComfyUI são difíceis de debugar em produção. Validação antecipada (campos obrigatórios, semver, comfyui.json, VRAM, provider disponível) previne erros silenciosos.

**Validator:** `src/infrastructure/validators/workflow_validator.py`
- `validate(manifest)` — validação estática
- `validate_runtime_compatibility(manifest, available_providers, available_vram_mb)` — validação de runtime
- `validate_or_raise(manifest)` — levanta `ValueError` se inválido
