# Examples

## payloads/

Payloads JSON prontos para testar cada workflow via `curl` ou qualquer cliente HTTP.

```bash
# Testar echo workflow
curl -X POST http://localhost:8000/v1/jobs \
  -H "Content-Type: application/json" \
  -d @examples/payloads/echo.json

# Testar image generation (requer workflow registrado)
curl -X POST http://localhost:8000/v1/jobs \
  -H "Content-Type: application/json" \
  -d @examples/payloads/image-generation.json
```

## integration/

Scripts Python demonstrando como integrar com a API.

```bash
# Submeter job e aguardar resultado
python examples/integration/submit_job.py
```

Requer servidor rodando:
```bash
uvicorn src.main:app --reload
# ou
docker-compose up api
```
