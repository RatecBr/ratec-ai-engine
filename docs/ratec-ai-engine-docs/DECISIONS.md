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

## WorkflowValidator obrigatório

**Decisão:** Todo workflow deve passar pelo `WorkflowValidator` antes de ser registrado ou executado.

**Motivo:** Falhas em workflows ComfyUI são difíceis de debugar em produção. Validação antecipada (campos obrigatórios, semver, comfyui.json, VRAM, provider disponível) previne erros silenciosos.

**Validator:** `src/infrastructure/validators/workflow_validator.py`
- `validate(manifest)` — validação estática
- `validate_runtime_compatibility(manifest, available_providers, available_vram_mb)` — validação de runtime
- `validate_or_raise(manifest)` — levanta `ValueError` se inválido
