# Память агентов — полная инструкция

Репозиторий **agent-memory** — единый шаблон для обмена контекстом между AI-агентами через git.

Поддерживаемые среды:

- **Cursor IDE** (локально) — hooks автоматически пишут события
- **Cursor Cloud Agent** — через SDK и PR
- **Antigravity** — через `GEMINI.md` + `AGENTS.md`
- **Codex / Claude Code** — через `AGENTS.md`

---

## Что лежит в репозитории

```
.agent/
  manifest.yaml      — декларация skills, MCP, plugins
  state.json         — этапы процесса, кто что делал
  HANDOFF.md         — контекст для следующего агента
  events.jsonl       — журнал действий (append-only)
  rules/             — правила для Antigravity
  bootstrap/         — установка skills/MCP в проект

AGENTS.md            — протокол для всех агентов
GEMINI.md            — инструкции для Antigravity

.cursor/
  hooks/             — автолог в Cursor IDE
  rules/             — правило alwaysApply
  skills/agent-bridge/

scripts/
  handoff.py         — мост Cloud ↔ Antigravity
  copy-into-repo.sh  — копирование в ваш проект
```

---

## Часть 1. Установка в свой проект

### Шаг 1 — скопировать шаблон

```bash
git clone https://github.com/tempersant/agent-memory.git ~/agent-memory

cd /path/to/your-project
~/agent-memory/scripts/copy-into-repo.sh .
```

Скрипт копирует `.agent/`, `AGENTS.md`, `GEMINI.md`, hooks, scripts. Существующие файлы не перезаписывает.

### Шаг 2 — bootstrap (skills + MCP)

```bash
pip install pyyaml
.agent/bootstrap/install.sh
```

Проверьте `.cursor/mcp.json` — секреты (`N8N_API_KEY` и т.д.) задайте в env, не в git.

### Шаг 3 — настроить этапы под свой процесс

Отредактируйте `.agent/state.json`:

```json
{
  "process_id": "my-feature-2026-06",
  "stage": "planning",
  "stages": {
    "planning":    { "status": "pending", "actor": null, "at": null, "notes": "" },
    "build":       { "status": "pending", "actor": null, "at": null, "notes": "" },
    "test":        { "status": "pending", "actor": null, "at": null, "notes": "" },
    "deploy":      { "status": "pending", "actor": null, "at": null, "notes": "" }
  }
}
```

Обновите `.agent/HANDOFF.md` — опишите текущую задачу.

### Шаг 4 — закоммитить в проект

```bash
git add .agent AGENTS.md GEMINI.md .cursor scripts
git commit -m "chore: add agent memory bridge"
git push
```

---

## Часть 2. Ежедневная работа

### Проверить статус процесса

```bash
python3 scripts/handoff.py status
```

Показывает этапы, actor, превью HANDOFF.

### Протокол для любого агента

**В начале сессии** — прочитать:

1. `.agent/HANDOFF.md`
2. `.agent/state.json`

**В конце сессии** — обновить:

1. `state.json` — status, actor, timestamp, artifacts
2. `HANDOFF.md` — секции: Current stage / Done / Next step / Do not touch
3. `events.jsonl` — одна строка-сводка (в Cursor hooks делают это сами)
4. Commit: `git commit -m "agent: handoff <stage>"`

---

## Часть 3. Cursor IDE (локально)

Hooks включены автоматически после копирования:

| Hook | Что делает |
|------|------------|
| `sessionStart` | читает HANDOFF, пишет в events.jsonl |
| `postToolUse` | логирует tool calls |
| `stop` | фиксирует завершение сессии |

Правило `.cursor/rules/agent-bridge.mdc` (`alwaysApply`) дублирует протокол, если hook не инжектит контекст.

**После работы в Cursor:**

```bash
git add .agent/
git commit -m "agent: handoff planning"
git push
```

---

## Часть 4. Antigravity

1. Откройте проект в Antigravity — автоматически загрузятся `GEMINI.md` + `AGENTS.md`
2. Агент читает `.agent/HANDOFF.md` и `state.json`
3. По завершении — обновляет `.agent/*` и коммитит

**Подготовить handoff в Antigravity:**

```bash
python3 scripts/handoff.py --to antigravity
```

Создаёт `.agent/ANTIGRAVITY_PROMPT.md` с готовым промптом (можно вставить в чат).

**После работы — передать Cloud:**

```bash
git push
export CURSOR_API_KEY="cursor_..."
python3 scripts/handoff.py --to cloud --repo owner/your-repo
```

---

## Часть 5. Cursor Cloud Agent

### Требования

```bash
pip install -r scripts/requirements.txt
export CURSOR_API_KEY="cursor_..."   # cursor.com/dashboard → Integrations
```

### Запуск

```bash
# Проверить промпт без запуска
python3 scripts/handoff.py --to cloud --repo owner/your-repo --dry-run

# Запустить Cloud Agent на следующий pending-этап
python3 scripts/handoff.py --to cloud --repo owner/your-repo

# Конкретный этап
python3 scripts/handoff.py --to cloud --repo owner/your-repo --stage build
```

Cloud Agent:

1. Клонирует репо
2. Читает `.agent/*`
3. Выполняет этап
4. Обновляет state + HANDOFF
5. Открывает PR `agent: handoff <stage>`

### После merge PR

```bash
python3 scripts/handoff.py sync
```

Подтянет изменения и покажет актуальный HANDOFF.

---

## Часть 6. Типичные сценарии

### Сценарий A: Antigravity планирует → Cloud строит → Antigravity ревьюит

```text
1. Antigravity: planning → commit .agent/ → push
2. handoff.py --to cloud --repo owner/repo
3. Merge PR от Cloud (implementation)
4. handoff.py sync
5. Antigravity: review → commit → push
6. handoff.py --to cloud (deploy)
```

### Сценарий B: Cursor local → Cloud → Cursor local

```text
1. Cursor: работа → hooks пишут events → commit .agent/
2. handoff.py --to cloud --repo owner/repo
3. Merge PR → handoff.py sync
4. Cursor: продолжить следующий этап
```

### Сценарий C: Только память без Cloud

Используйте `.agent/` вручную — любой агент читает HANDOFF в начале и пишет в конце. Скрипты не обязательны.

---

## Часть 7. Настройка manifest.yaml

В `.agent/manifest.yaml` объявляйте capabilities проекта:

```yaml
skills:
  - source: .cursor/skills/agent-bridge
    scope: project
  - source: ~/.cursor/skills/my-skill
    scope: personal
    optional: true

mcp:
  merge_into: .cursor/mcp.json
  servers:
    my-mcp:
      command: npx
      args: ["-y", "some-mcp"]
      env:
        API_KEY: "${MY_API_KEY}"
```

После изменений: `.agent/bootstrap/install.sh`

**Важно:** personal skills (`~/.cursor/skills/`) на Cloud не попадут — дублируйте нужное в `.cursor/skills/` репо.

---

## Часть 8. Поля state.json

| Поле | Значение |
|------|----------|
| `status` | `pending` / `in_progress` / `done` / `blocked` |
| `actor` | `antigravity`, `cursor-local`, `cursor-cloud:bc-xxx`, `codex` |
| `at` | ISO-8601 UTC, напр. `2026-06-07T12:00:00Z` |
| `artifacts` | пути файлов, URL PR, ссылки |

---

## Часть 9. Обновление шаблона

Когда в `agent-memory` появляются улучшения:

```bash
cd ~/agent-memory && git pull
~/agent-memory/scripts/copy-into-repo.sh /path/to/your-project
# Смержите вручную, если copy-into-repo.sh пропустил существующие файлы
```

---

## Часть 10. Troubleshooting

| Проблема | Решение |
|----------|---------|
| Cloud не видит изменения | `git push` перед `--to cloud` |
| `CURSOR_API_KEY` invalid | Новый ключ в Dashboard → Integrations |
| Hooks не срабатывают | Перезапустить Cursor; проверить Hooks output channel |
| Antigravity не читает HANDOFF | Включить AGENTS.md в Settings → Agent |
| Symlinks skills сломаны | Запустить `.agent/bootstrap/install.sh` |
| Конфликт в state.json | Разрешить в git, затем `handoff.py status` |

---

## Быстрая шпаргалка

```bash
# Статус
python3 scripts/handoff.py status

# → Antigravity
python3 scripts/handoff.py --to antigravity

# → Cloud
export CURSOR_API_KEY="cursor_..."
python3 scripts/handoff.py --to cloud --repo owner/repo

# После PR
python3 scripts/handoff.py sync

# Bootstrap
.agent/bootstrap/install.sh

# Копировать в новый проект
~/agent-memory/scripts/copy-into-repo.sh /path/to/project
```

---

## Ссылки

- Репозиторий: https://github.com/tempersant/agent-memory
- Cursor API key: https://cursor.com/dashboard/integrations
- Cloud Agents: https://cursor.com/docs/cloud-agent
