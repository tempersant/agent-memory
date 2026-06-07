# Конспект диалога: Память агентов (Agent Memory)

> Документ для передачи контекста в Claude, Antigravity, Codex или любой другой агент.
> Дата: 2026-06-07

---

## Задача

Сделать **мост между Cloud Agent (Cursor), Cursor IDE, Antigravity и другими моделями**, чтобы агенты:

1. Знали, **кто что сделал** и **на каком этапе** процесс
2. **Синхронизировали** skills, rules, MCP между средами
3. Могли **передавать работу** друг другу без потери контекста

---

## Решение (архитектурное)

Выбран подход **git-native** — единый источник правды в репозитории, без отдельного сервера (Bridge API отложен на потом).

### Три слоя

| Слой | Что это | Статус |
|------|---------|--------|
| **0 — Git** | `.agent/state.json`, `HANDOFF.md`, `events.jsonl`, `AGENTS.md` | ✅ Сделано |
| **1 — Bootstrap** | `manifest.yaml` + `install.sh` — skills, rules, MCP | ✅ Сделано |
| **2 — Cursor hooks** | sessionStart, postToolUse, stop | ✅ Сделано |
| **3 — SDK** | `handoff.py --to cloud` — Cloud Agent | ✅ Сделано |
| **4 — Bridge API** | Real-time очередь Mac ↔ Cloud | ⏸ Отложено |

### Почему git, а не API

- Работает с **любой** моделью (Cursor, Cloud, Antigravity, Codex)
- Версионируется, можно откатить
- Не зависит от вендора
- Cloud видит state только после `git push`; Antigravity читает файлы локально

---

## Репозиторий

**https://github.com/tempersant/agent-memory**

Локально: `~/Documents/Projects/agent-memory` (бывш. `agent-bridge-template`)

### Структура

```
.agent/
  manifest.yaml       — декларация skills, MCP, plugins
  state.json          — этапы, actor, artifacts
  HANDOFF.md          — контекст для следующего агента
  events.jsonl        — журнал (append-only)
  rules/              — правила Antigravity
  bootstrap/          — install.sh / install.py

AGENTS.md             — протокол для ВСЕХ агентов
GEMINI.md             — инструкции для Antigravity
INSTRUCTION_RU.md     — полная инструкция на русском

.cursor/
  hooks/              — автолог в Cursor IDE
  rules/agent-bridge.mdc
  skills/agent-bridge/

scripts/
  handoff.py          — мост Cloud ↔ Antigravity
  copy-into-repo.sh   — копирование в проект
  cloud-handoff.py    — обёртка (→ handoff.py --to cloud)
```

---

## Протокол handoff (обязателен для каждого агента)

### В начале сессии

1. Прочитать `.agent/HANDOFF.md`
2. Прочитать `.agent/state.json`
3. Не брать этап `in_progress` у другого actor без явного указания в HANDOFF

### В конце сессии

1. Обновить `state.json`: `status`, `actor`, `at`, `artifacts`
2. Переписать `HANDOFF.md` (секции: Current stage / Done / Next step / Do not touch)
3. Append в `events.jsonl`
4. Commit: `git commit -m "agent: handoff <stage>"`

### Значения actor

- `antigravity`
- `cursor-local`
- `cursor-cloud:bc-<agent-id>`
- `codex`

---

## Команды

```bash
# Статус процесса
python3 scripts/handoff.py status

# Подготовить работу в Antigravity
python3 scripts/handoff.py --to antigravity

# Отдать этап Cloud Agent
export CURSOR_API_KEY="cursor_..."
python3 scripts/handoff.py --to cloud --repo owner/repo

# После merge PR от Cloud
python3 scripts/handoff.py sync

# Установка в новый проект
git clone https://github.com/tempersant/agent-memory.git ~/agent-memory
~/agent-memory/scripts/copy-into-repo.sh /path/to/project
pip install pyyaml && .agent/bootstrap/install.sh
```

---

## Сценарии Cloud ↔ Antigravity

### Antigravity → Cloud

```
Antigravity делает этап
  → обновляет .agent/*
  → git commit + push
  → handoff.py --to cloud --repo owner/repo
Cloud Agent читает .agent/*, делает следующий этап, открывает PR
```

### Cloud → Antigravity

```
Merge PR от Cloud
  → handoff.py sync (git pull + HANDOFF)
  → открыть проект в Antigravity (GEMINI.md + AGENTS.md грузятся сами)
  → опционально: handoff.py --to antigravity
Antigravity продолжает по HANDOFF.md
```

### Cursor local ↔ Cloud

```
Cursor: hooks пишут events.jsonl автоматически
  → commit .agent/
  → handoff.py --to cloud
Merge PR → handoff.py sync → продолжить в Cursor
```

---

## Адаптеры по средам

| Среда | Как подключается |
|-------|------------------|
| **Cursor IDE** | hooks + rule `alwaysApply` + `.cursor/skills/` |
| **Cloud Agent** | SDK `handoff.py --to cloud`, читает `.agent/*` из клона репо |
| **Antigravity** | `GEMINI.md` + `AGENTS.md` + `.agent/rules/` |
| **Codex / Claude Code** | `AGENTS.md` в корне репо |

**Нет** прямого API между Cloud и Antigravity — только git.

---

## Важные ограничения

1. Personal skills (`~/.cursor/skills/`) **не попадают** на Cloud — дублировать в `.cursor/skills/` репо
2. MCP-секреты — только в env / dashboard, не в git
3. Cloud не видит локальные изменения без `git push`
4. Antigravity не имеет Cursor hooks — handoff в конце сессии вручную (по GEMINI.md)
5. `sessionStart` hook в Cursor может не инжектить контекст (баг IDE) — страховка: rule `agent-bridge.mdc`

---

## Что НЕ сделано (намеренно)

- **Bridge API** (уровень 4) — real-time очередь, heartbeat; добавим когда git-handoff станет узким местом
- Автокоммит из hooks — только логирование; commit делает агент/пользователь

---

## Инструкции для агента-получателя

Если ты **Claude / Antigravity / Codex** и получил этот конспект:

1. Клонируй или открой проект с установленным agent-memory (`copy-into-repo.sh`)
2. Прочитай `AGENTS.md`, `GEMINI.md` (Antigravity), `.agent/HANDOFF.md`, `.agent/state.json`
3. Выполни текущий `stage` из state.json
4. Обнови `.agent/*` и закоммить по протоколу выше
5. Для Cloud: `python3 scripts/handoff.py --to cloud --repo owner/repo`

Полная документация: **INSTRUCTION_RU.md** в репозитории agent-memory.

---

## История решений в диалоге

1. Обсудили проблему: Cloud, Cursor, Antigravity не делят контекст
2. Сравнили варианты: git vs bridge API vs только SDK
3. Выбрали **git-native + тонкие адаптеры** как долгосрочное решение
4. Собрали шаблон уровней 0–3 (без Bridge API)
5. Добавили адаптер Antigravity: `GEMINI.md`, `handoff.py --to antigravity`
6. Создали репозиторий **agent-memory**, запушили на GitHub
7. Написали `INSTRUCTION_RU.md` — полная инструкция

---

## Ссылки

- Repo: https://github.com/tempersant/agent-memory
- Cursor API key: https://cursor.com/dashboard/integrations
- Cloud Agents docs: https://cursor.com/docs/cloud-agent
