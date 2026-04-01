# Cloud.ru Skills for OpenClaw

## Project overview

A collection of skills for the OpenClaw agent targeting the cloud.ru provider. Each skill is a self-contained folder with a `SKILL.md` entry point and optional scripts/references/assets.

## Skill authoring guide

The file `openclaw-skill-authoring-guide.md` is the canonical reference for writing skills. Always follow it when creating or modifying skills.

Key rules:
- Every skill must have `SKILL.md` with YAML frontmatter (`name`, `description` required)
- `metadata` field must be **single-line JSON**, not multi-line YAML
- Use `{baseDir}` for all local file references inside `SKILL.md`
- Keep `SKILL.md` short and procedural; put complex logic in `scripts/`
- Never embed secrets in `SKILL.md`
- Dependencies go in `metadata.openclaw.requires` (`bins`, `anyBins`, `env`, `config`)

## Skill folder structure

```
<skill-name>/
├── SKILL.md              # Required entry point
├── scripts/              # Executable scripts the agent runs
├── references/           # API docs, examples, schemas
└── assets/               # Templates, static files
```

## Existing skills

- `cloudru-account-setup` — creates Cloud.ru service account and Foundation Models API key via browser-assisted or manual flow. Script uses only Python stdlib.
- `cloudru-foundation-models` — working with Cloud.ru Foundation Models API: model catalog, cURL/Python examples, OpenClaw provider setup. Requires `CLOUD_RU_FOUNDATION_MODELS_API_KEY`.
- `cloudru-ml-inference` — full CRUD and inference for Cloud.ru ML Inference (Model RUN). Deploy, manage, and call ML models on GPU. Requires `CP_CONSOLE_KEY_ID`, `CP_CONSOLE_SECRET`, `PROJECT_ID` and the `inference-clients` SDK.

## Conventions

- Skill names use kebab-case for folders, snake_case or kebab-case for the `name` field
- Scripts should minimize external dependencies (prefer stdlib)
- Reference docs go in `references/`, not inline in `SKILL.md`
- Russian is fine for user-facing text; code and identifiers in English
