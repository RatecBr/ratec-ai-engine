# Como adicionar um novo Provider ou Backend

## Referência: ComfyUI (implementação real)

O ComfyUI é o provider de imagem em produção. Use como referência ao criar novos providers.

```
src/infrastructure/providers/comfyui/
├── __init__.py           # exports públicos
├── client.py             # ComfyUIClient
├── exceptions.py         # exceções tipadas
├── job_executor.py       # ComfyUIJobExecutor
├── models.py             # response models
├── provider.py           # ComfyUIProvider(BaseProvider)
├── result_parser.py      # ComfyUIResultParser
└── workflow_loader.py    # ComfyUIWorkflowLoader
```

---

## Adicionar um ExecutionBackend

Um `ExecutionBackend` é onde o compute roda (ComfyUI, RunPod, Modal, Replicate, AWS, etc.).

### 1. Criar a implementação

```python
# src/infrastructure/execution/modal_backend.py
from src.infrastructure.execution.base_backend import BaseExecutionBackend
from src.domain.entities.execution import ExecutionContext, ExecutionResult, ExecutionStatus

class ModalBackend(BaseExecutionBackend):
    def __init__(self, api_key: str, app_name: str) -> None:
        self._api_key = api_key
        self._app_name = app_name

    @property
    def backend_id(self) -> str:
        return "modal"

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        # implementar chamada ao Modal API
        ...

    async def health_check(self) -> bool:
        ...

    def supports_strategy(self, strategy: str) -> bool:
        return strategy in ("auto", "serverless", "modal")
```

### 2. Registrar no ExecutionManager

Em `src/config/dependencies.py`, dentro de `_build_execution_manager()`:

```python
if settings.modal_api_key:
    manager.register_backend(ModalBackend(settings.modal_api_key, settings.modal_app_name))
```

A ordem de prioridade atual: `("runpod", "comfyui", "modal", "replicate", "aws", "azure", "kubernetes")`

### 3. Adicionar variáveis de ambiente

Em `.env.example`:
```
MODAL_API_KEY=your_modal_api_key
MODAL_APP_NAME=ratec-ai-engine
```

---

## Adicionar um Provider de capability

Um Provider representa um serviço de IA no catálogo `/v1/providers`.

```python
# src/infrastructure/providers/stability/provider.py
class StabilityProvider(BaseProvider):
    def __init__(self, api_key: str) -> None:
        super().__init__(Provider(
            id="stability",
            name="Stability AI",
            type=ProviderType.STABILITY,  # adicionar ao enum se necessário
            capabilities=["image-generation", "image-to-image"],
        ))
```

Registrar em `src/config/dependencies.py`:
```python
if settings.stability_api_key:
    provider_registry.register(StabilityProvider(settings.stability_api_key))
```

---

## Criar exceptions tipadas para o provider

Siga o padrão do ComfyUI:

```python
# src/infrastructure/providers/meu_provider/exceptions.py
class MeuProviderError(Exception): ...
class MeuProviderConnectionError(MeuProviderError): ...
class MeuProviderTimeoutError(MeuProviderError): ...
class MeuProviderExecutionError(MeuProviderError): ...
```

O `ExecutionBackend` deve capturar essas exceptions e converter para `ExecutionResult(status=FAILED)`.

---

## Adicionar suporte a novo modelo

1. Adicionar `metadata.yaml` em `models/<model-id>/`
2. Registrar no `ModelRegistry` em `src/config/dependencies.py`
3. Registrar as capabilities no `CapabilityRegistry`

---

## Checklist

- [ ] Criar diretório em `src/infrastructure/providers/<nome>/`
- [ ] Implementar `<Nome>Provider(BaseProvider)`
- [ ] Implementar `<Nome>Backend(BaseExecutionBackend)` se for um backend de execução
- [ ] Criar exceptions tipadas
- [ ] Registrar em `src/config/dependencies.py`
- [ ] Adicionar variáveis de ambiente ao `.env.example`
- [ ] Registrar no `WorkflowValidator` se necessário
