# Как правильно создать скилл для OpenClaw

_Актуализировано по документации OpenClaw на 2026-03-25._

## 1. Что такое скилл в OpenClaw

Скилл в OpenClaw — это папка, внутри которой обязательно есть файл `SKILL.md`. В этом файле лежат:

- YAML frontmatter с метаданными скилла;
- markdown-инструкция для агента: когда применять скилл, какими инструментами пользоваться, в каком порядке действовать;
- при необходимости — описание зависимостей, ограничений и ссылок на скрипты/ресурсы внутри папки скилла.

Проще всего думать о скилле как о «пакете инструкций + вспомогательных файлов», который подключается к системному промпту агента.

---

## 2. Где OpenClaw ищет скиллы

OpenClaw загружает скиллы из нескольких мест.

Приоритет такой:

1. `<workspace>/skills` — самый высокий приоритет;
2. `~/.openclaw/skills` — общий каталог для локальных/managed скиллов;
3. встроенные bundled skills — самый низкий приоритет.

Дополнительно можно подключить другие папки через `skills.load.extraDirs` в `~/.openclaw/openclaw.json`. У них самый низкий приоритет.

### Практическое правило

- Если скилл нужен только конкретному агенту или проекту — кладите его в `<workspace>/skills/<skill-name>/`.
- Если скилл должен быть доступен всем агентам на машине — кладите в `~/.openclaw/skills/<skill-name>/`.

Обычно для локальной разработки удобнее использовать workspace-вариант.

---

## 3. Минимальная структура скилла

Минимально достаточно одной папки и одного файла:

```text
my-skill/
└── SKILL.md
```

Но на практике лучше сразу использовать такую структуру:

```text
my-skill/
├── SKILL.md
├── scripts/
│   └── run.py
├── references/
│   └── usage.md
└── assets/
    └── example.json
```

### Что обычно хранить

- `SKILL.md` — обязательная точка входа;
- `scripts/` — исполняемые скрипты, которые агент будет запускать;
- `references/` — вспомогательная документация, примеры API, схемы запросов;
- `assets/` — шаблоны, JSON, примеры данных, статические файлы.

---

## 4. Обязательный файл `SKILL.md`

У каждого скилла должен быть `SKILL.md` с YAML frontmatter.

Минимальный рабочий шаблон:

```markdown
---
name: hello_world
description: A simple skill that says hello.
---

# Hello World Skill

Когда пользователь просит приветствие, используй доступный инструмент
для вывода текста и верни фразу "Hello from your custom skill!".
```

### Обязательные поля

- `name` — уникальный идентификатор скилла;
- `description` — короткое описание, которое увидит агент.

### Правила для `SKILL.md`

1. `name` лучше писать в `snake_case` или в стабильном машинном виде без случайных пробелов.
2. `description` должна быть короткой и предметной.
3. YAML frontmatter должен быть в начале файла.
4. Парсер embedded-agent в OpenClaw поддерживает только **однострочные ключи frontmatter**.
5. Поле `metadata`, если используется, нужно держать как **однострочный JSON-объект**, а не как многострочную YAML-структуру.
6. Для ссылок на файлы внутри скилла используйте `{baseDir}`.

Пример ссылки на локальный файл внутри инструкции:

```markdown
Открой файл `{baseDir}/references/usage.md` и следуй инструкции из него.
```

---

## 5. Рекомендуемый шаблон `SKILL.md`

Ниже шаблон, который подходит для большинства production-скиллов:

```markdown
---
name: my_skill
description: Выполняет специализированный workflow для конкретной задачи.
metadata: {"openclaw":{"emoji":"🛠️","requires":{"bins":["python3"],"config":["browser.enabled"]},"primaryEnv":"MY_SKILL_API_KEY"}}
---

# Назначение

Этот скилл помогает агенту выполнять <ваш сценарий>.

# Когда использовать

Используй этот скилл, когда пользователь:
- просит <сценарий 1>;
- просит <сценарий 2>;
- явно упоминает <система / API / продукт>.

# Порядок действий

1. Проверь, что доступны нужные инструменты и зависимости.
2. При необходимости запроси недостающие данные через разрешенные инструменты.
3. Выполни основной workflow.
4. Сохрани артефакты в понятном виде.
5. Верни пользователю итог и следующие шаги.

# Локальные ресурсы

- Скрипт: `{baseDir}/scripts/run.py`
- Документация: `{baseDir}/references/usage.md`

# Ограничения

- Не выводи секреты в ответ пользователю.
- Не запускай опасные команды с непроверенным пользовательским вводом.
```

---

## 6. Полезные поля frontmatter

Кроме `name` и `description`, OpenClaw поддерживает дополнительные поля.

### Часто используемые

- `homepage` — ссылка, которая показывается в UI как Website;
- `user-invocable: true|false` — можно ли вызывать скилл как пользовательскую slash-команду;
- `disable-model-invocation: true|false` — скрыть скилл из model prompt, но оставить доступным для прямого вызова;
- `command-dispatch: tool` — отправлять slash-команду сразу в tool, минуя модель;
- `command-tool` — имя инструмента для direct dispatch;
- `command-arg-mode: raw` — пробрасывать строку аргументов без разбора.

### Что важно помнить

Если вы используете `command-dispatch: tool`, OpenClaw вызывает tool с параметрами такого вида:

```json
{
  "command": "<raw args>",
  "commandName": "<slash command>",
  "skillName": "<skill name>"
}
```

---

## 7. `metadata.openclaw`: как правильно указывать зависимости

OpenClaw умеет фильтровать скиллы на этапе загрузки. Для этого используется `metadata.openclaw`.

Пример:

```markdown
---
name: image-lab
description: Generate or edit images via a provider-backed image workflow
metadata: {"openclaw":{"requires":{"bins":["uv"],"env":["GEMINI_API_KEY"],"config":["browser.enabled"]},"primaryEnv":"GEMINI_API_KEY"}}
---
```

### Основные поля `metadata.openclaw`

- `always: true` — всегда считать скилл eligible;
- `emoji` — эмодзи для UI;
- `homepage` — сайт скилла;
- `os` — список поддерживаемых платформ: `darwin`, `linux`, `win32`;
- `requires.bins` — все бинарники должны существовать в `PATH`;
- `requires.anyBins` — достаточно хотя бы одного бинарника;
- `requires.env` — нужные env-переменные должны быть доступны;
- `requires.config` — требуемые пути в `openclaw.json` должны быть truthy;
- `primaryEnv` — главная env-переменная, с которой связывается `skills.entries.<name>.apiKey`;
- `install` — инструкции по установке для UI.

### Важное ограничение

`metadata` нужно писать как **single-line JSON**. Это частая ошибка. Нельзя полагаться на красивый многострочный YAML-объект, если вы хотите максимально совместимое поведение с текущим парсером OpenClaw.

---

## 8. Как подключать секреты и конфиг

Все настройки скиллов лежат в `~/.openclaw/openclaw.json`, секция `skills`.

Пример:

```json5
{
  skills: {
    load: {
      extraDirs: ["~/Projects/shared-skills"],
      watch: true,
      watchDebounceMs: 250,
    },
    entries: {
      "my-skill": {
        enabled: true,
        apiKey: { source: "env", provider: "default", id: "MY_SKILL_API_KEY" },
        env: {
          MY_SKILL_API_KEY: "secret-value",
        },
        config: {
          endpoint: "https://example.invalid",
          model: "example-model",
        },
      },
    },
  },
}
```

### Как это работает

- `enabled: false` — отключает скилл;
- `env` — добавляет переменные окружения на время agent run, если они еще не заданы;
- `apiKey` — удобный способ подать ключ для скилла, который объявил `primaryEnv`;
- `config` — место для кастомных параметров скилла;
- `load.extraDirs` — дополнительные папки со скиллами;
- `load.watch` — автоподхват изменений;
- `load.watchDebounceMs` — debounce для watcher.

### Важный нюанс

Если имя скилла содержит дефисы, ключ в `entries` лучше явно писать в кавычках:

```json5
entries: {
  "cloudru-foundation-models": {
    enabled: true
  }
}
```

Если скилл использует `metadata.openclaw.skillKey`, то в `skills.entries` нужно использовать именно этот ключ.

---

## 9. Как правильно активировать новый скилл

После создания или изменения скилла используйте один из способов:

```bash
# внутри чата OpenClaw
/new

# либо перезапуск gateway
openclaw gateway restart
```

Проверить, что скилл виден OpenClaw:

```bash
openclaw skills list
openclaw skills list --eligible
openclaw skills info <name>
openclaw skills check
```

### Что важно знать про refresh

- OpenClaw делает snapshot eligible skills в начале сессии;
- изменения обычно гарантированно подхватываются в новой сессии;
- при включенном watcher список может обновиться и в текущей сессии на следующем agent turn.

---

## 10. Как тестировать скилл

Простейший цикл разработки:

```bash
mkdir -p ~/.openclaw/workspace/skills/my-skill
$EDITOR ~/.openclaw/workspace/skills/my-skill/SKILL.md
openclaw gateway restart
openclaw skills list
openclaw agent --message "выполни сценарий моего скилла"
```

### Что проверять в первую очередь

1. Скилл вообще появился в `openclaw skills list`.
2. Скилл стал eligible, если у него есть `requires.*`.
3. Все пути в инструкции корректны.
4. Внешние бинарники реально есть в `PATH`.
5. Секреты не печатаются в ответах.
6. Агент понимает, когда нужно применять скилл, а когда нет.

---

## 11. Особенности sandbox

Если агент работает в sandbox, есть важный нюанс:

- `requires.bins` проверяется на **host** во время загрузки скилла;
- но если сам скилл запускается внутри контейнера, нужный бинарник должен быть установлен **и внутри контейнера**.

Для этого обычно используют:

- `agents.defaults.sandbox.docker.setupCommand`;
- либо кастомный образ sandbox.

Также для установки зависимостей внутри sandbox нужны:

- сетевой доступ;
- writable root filesystem;
- root user внутри sandbox.

И еще один важный момент: `skills.entries.<skill>.env` и `skills.entries.<skill>.apiKey` применяются к **host-run**, а не автоматически к sandbox-контейнеру. Для sandbox env нужно отдельно задавать docker env в настройках sandbox.

---

## 12. Безопасные практики

### Делайте так

- держите `SKILL.md` коротким и процедурным;
- явно прописывайте, когда скилл использовать;
- храните сложную логику в `scripts/`, а не в длинном промпте;
- используйте `{baseDir}` вместо хрупких абсолютных путей;
- ограничивайте исполнение через `requires.bins`, `requires.env`, `requires.config`;
- тестируйте скилл на безопасных примерах до публикации.

### Не делайте так

- не вставляйте секреты прямо в `SKILL.md`;
- не позволяйте пользователю напрямую подставлять произвольные shell-команды в `exec` без валидации;
- не держите весь workflow в одном гигантском markdown без структуры;
- не полагайтесь на то, что sandbox magically унаследует env с хоста.

---

## 13. Шаблон production-структуры

Готовый каркас:

```text
<workspace>/skills/my-skill/
├── SKILL.md
├── scripts/
│   ├── bootstrap.py
│   └── helpers.py
├── references/
│   ├── api.md
│   └── examples.md
└── assets/
    ├── request-template.json
    └── response-template.json
```

Пример `SKILL.md`:

```markdown
---
name: my-skill
description: Подключает внешний сервис и выполняет предметный workflow.
metadata: {"openclaw":{"emoji":"🔌","requires":{"bins":["python3"],"env":["MY_SKILL_API_KEY"]},"primaryEnv":"MY_SKILL_API_KEY"}}
---

# Когда использовать

Используй этот скилл, когда пользователь просит работать с сервисом My Service.

# Шаги

1. Проверь наличие ключа `MY_SKILL_API_KEY`.
2. При необходимости прочитай `{baseDir}/references/api.md`.
3. Запусти `{baseDir}/scripts/bootstrap.py`.
4. Верни пользователю итог, не раскрывая секреты.

# Ограничения

- Не логируй API keys.
- Не выполняй опасные команды с непроверенным вводом.
```

---

## 14. Как опубликовать или установить готовый скилл

Для локальной установки:

```bash
openclaw skills install <skill-slug>
openclaw skills update <skill-slug>
openclaw skills update --all
```

Для просмотра локальных скиллов:

```bash
openclaw skills list
openclaw skills info <name>
openclaw skills check
```

ClawHub — это публичный реестр скиллов OpenClaw. Его удобно использовать для discovery, install и update.

---

## 15. Короткий чеклист перед использованием

Перед тем как считать скилл «правильно сделанным», проверь:

- есть папка скилла и внутри `SKILL.md`;
- `name` и `description` заполнены;
- `metadata` записан в single-line JSON, если используется;
- все локальные ссылки идут через `{baseDir}`;
- зависимости описаны через `requires.*`;
- секреты вынесены в `skills.entries.*.env` или `apiKey`;
- скилл виден в `openclaw skills list`;
- скилл eligible там, где должен быть eligible;
- поведение проверено на реальном тестовом сообщении.

---

## 16. Самая короткая рабочая инструкция

Если нужен буквально минимальный путь:

```bash
mkdir -p ~/.openclaw/workspace/skills/my-skill
cat > ~/.openclaw/workspace/skills/my-skill/SKILL.md <<'MD'
---
name: my_skill
description: Делает одну полезную вещь.
---

# Когда использовать
Используй этот скилл, когда пользователь просит сделать одну полезную вещь.

# Что делать
1. Выполни нужные действия.
2. Верни результат.
MD

openclaw gateway restart
openclaw skills list
```

Этого уже достаточно, чтобы OpenClaw увидел новый пользовательский скилл.

---

## 17. Источники

Этот гайд собран по официальной документации OpenClaw:

- Skills
- Creating Skills
- Skills Config
- CLI: `openclaw skills`

Если захотите, на основе этого гайда можно сразу сгенерировать шаблон-папку нового скилла под ваш конкретный use case.
