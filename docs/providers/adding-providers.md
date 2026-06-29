# Como adicionar um novo Provider ou Backend

## Adicionar um ExecutionBackend

Um `ExecutionBackend` é onde o compute roda (RunPod, Modal, Replicate, AWS, etc.).

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

### 3. Adicionar variáveis de ambiente

Em `.env.example`:
```
MODAL_API_KEY=your_modal_api_key
MODAL_APP_NAME=ratec-ai-engine
```

## Adicionar um Provider de capability

Um Provider representa um serviço de IA no catálogo `/v1/providers`.

```python
# src/infrastructure/providers/stability_provider.py
class StabilityProvider(BaseProvider):
    def __init__(self, api_key: str) -> None:
        super().__init__(Provider(
            id="stability",
            name="Stability AI",
            type=ProviderType.STABILITY,  # adicionar ao enum se necessário
            capabilities=["image-generation", "image-to-image"],
        ))
```

## Adicionar suporte a novo modelo

1. Adicionar `metadata.yaml` em `models/<model-id>/`
2. Registrar no `ModelRegistry` em `src/config/dependencies.py`
3. Registrar as capabilities no `CapabilityRegistry`
