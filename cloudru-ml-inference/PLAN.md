# Plan: Mini-SDK для замены inference-clients

## Цель
Заменить все зависимости от `pkg.sbercloud.tech` (`inference-clients`, `evoapp-http-clients`, `http_client_retries`, `evoapp-common`, `pydantic-extensions`) одним файлом `cloudru_client.py` на базе `httpx`.

## Что нужно реализовать в cloudru_client.py

### 1. IAM Auth (~30 строк)
- POST `https://iam.api.cloud.ru/api/v1/auth/token` с `{"keyId": ..., "secret": ...}`
- Ответ: `{"access_token": "...", "id_token": "...", "expires_in": ...}`
- Кеширование токена в памяти
- Автообновление при 401/403 (retry once)

### 2. BFF Client — управление model runs (~80 строк)
Base URL: `https://console.cloud.ru`
API prefix: `/u-api/inference/model-run/v1`

Методы:
- `list_model_runs(project_id, limit, offset)` — GET `/{project_id}/modelruns`
- `get_model_run(project_id, model_run_id)` — GET `/{project_id}/modelruns/{id}`
- `create_model_run(project_id, payload)` — POST `/{project_id}/modelruns`
- `update_model_run(project_id, model_run_id, payload)` — PUT `/{project_id}/modelruns/{id}`
- `delete_model_run(project_id, model_run_id)` — DELETE `/{project_id}/modelruns/{id}`
- `suspend_model_run(project_id, model_run_id)` — PATCH `/{project_id}/modelruns/{id}/suspend`
- `resume_model_run(project_id, model_run_id)` — PATCH `/{project_id}/modelruns/{id}/resume`
- `get_history(project_id, model_run_id)` — GET `/{project_id}/modelruns/{id}/history`
- `get_quotas(project_id)` — GET `/{project_id}/quota-usage`
- `get_frameworks(project_id, limit, offset)` — GET `/{project_id}/runtime-templates`
- `get_catalog(params)` — GET `/predefined-models`
- `get_catalog_detail(model_card_id)` — GET `/predefined-models/{id}`

### 3. Inference Client — вызов моделей (~40 строк)
Base URL: `https://{model_run_id}.modelrun.inference.cloud.ru`

Методы:
- `chat(model_run_id, payload, use_auth)` — POST `/v1/chat/completions`
- `embed(model_run_id, payload, use_auth)` — POST `/v1/embeddings`
- `rerank(model_run_id, payload, use_auth)` — POST `/v1/rerank`
- `ping(model_run_id, use_auth)` — GET `/v1/models`

### 4. Retry logic (~15 строк)
- Простой retry с exponential backoff для 502/503/504
- Retry на connection errors
- Макс 3 попытки (не 8 как в SDK — для CLI достаточно)

## Файловая структура

```
scripts/
├── cloudru_client.py          # IAMAuth + CloudruInferenceClient + retry
├── helpers.py                 # get_env, build_client, check_response, print_json, enum maps
├── commands/
│   ├── __init__.py            # re-export COMMANDS dict
│   ├── catalog.py             # catalog, catalog_detail, deploy
│   ├── crud.py                # list, get, create, update, delete, suspend, resume
│   ├── inference.py           # call, embed, rerank, ping
│   └── info.py                # history, quotas, frameworks
└── ml_inference.py            # argparse + dispatch (entry point)
```

## План изменений

### Шаг 1: Создать `scripts/cloudru_client.py` ✅
### Шаг 2: Создать `scripts/helpers.py` ✅
### Шаг 3: Создать `scripts/commands/*.py` ✅
### Шаг 4: Переписать `scripts/ml_inference.py` (только argparse + dispatch) ✅
### Шаг 5: Обновить `SKILL.md` ✅
### Шаг 6: Обновить `references/examples.md` ✅
### Шаг 7: Обновить `references/api-reference.md` ✅
