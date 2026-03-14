# Shraavasti Bhat — Claude Code Global Context

## About Me
- **GitHub:** `shraavb`
- **Background:** Student + builder — robotics, AI agents, full-stack web
- **Current focus areas:** Robotics (LeRobot / ROS / Isaac Sim), AI agents (AdminifAI callbot), Senior Design (SpeakEasy), ML research (ego4d RL)

---

## Active Projects

| Project | Location | Stack | Description |
|---|---|---|---|
| **AdminifAI** | `~/AdminifAI/` | Flask, Next.js, Twilio, Deepgram, ElevenLabs, Ollama | AI-powered admin scheduling platform with voice bot |
| **callbot-adminifAI** | `~/callbot-adminifAI/` | Python, WebSocket, Deepgram, ElevenLabs | Voice call pipeline for AdminifAI |
| **SpeakEasy** (Senior Design) | `~/-Senior-Design-SpeakEasy/` | React, Node.js, AWS | Language learning / fluency app |
| **ego4d RL** | `~/ego4d_rl_project/` | Python, PyTorch | Ego4D dataset + hierarchical RL research |
| **LeRobot** | `~/lerobot/` | Python, PyTorch | Robot learning / pick-and-place |
| **Orbit** | `~/Orbit-your-personal-agent/` | Python | Personal agent project |
| **Procura** | `~/Procura/` | Python/Flask backend | — |
| **Mind Palace** | `~/Shraav-sMindPalace-2/` | Vue.js | Personal portfolio / project showcase |

---

## Tech Stack

### Languages
- **Python** (primary), **TypeScript/JavaScript**, **R** (for stats)

### Frontend
- React, Next.js, Vue.js, Vite, Ionic/Capacitor

### Backend
- Flask, Node.js/Express, PostgreSQL, Celery, Gunicorn

### AI / ML
- PyTorch, HuggingFace, Ollama (local LLMs: `qwen3:32b`)
- Deepgram (STT/TTS), ElevenLabs (TTS), Groq

### Robotics
- LeRobot, Isaac Sim, ROS, Jetbot/Waveshare

### DevOps / Infra
- Docker, ngrok, GitHub Actions, Netlify, Homebrew

### Key Services
- Twilio (voice/SMS), GitHub (`gh` CLI), AWS (S3/EC2)

---

## Environment

- **OS:** macOS (Darwin 24.6.0, Apple Silicon)
- **Shell:** zsh — reload with `source ~/.zshrc`
- **Python envs:** `.venv/` per project (activate with `source .venv/bin/activate`)
- **Node:** npm / npx
- **Claude Code settings:** `~/.claude/settings.json`

---

## Coding Principles

- **DRY** — Do not repeat yourself
  - Extract repeated logic into a shared function/module instead of copy-pasting
  - Bad: validating an email in 3 different route handlers; Good: one `validate_email()` util called everywhere
  - If you write the same block twice, stop and abstract it

- **KISS** — Keep it simple, stupid
  - Prefer the obvious, readable solution over the clever one
  - Bad: a recursive one-liner that requires a comment to explain; Good: a clear loop anyone can read
  - Don't add config flags, base classes, or abstractions for a single use case

- **SRP** — Single responsibility principle
  - Each function, class, or module should do one thing and do it well
  - Bad: a `processOrder()` that validates input, charges the card, updates DB, and sends email; Good: four separate functions each doing one step
  - If you have to use "and" to describe what a function does, split it

## Workflow Preferences

- Use `lazygit` for interactive git UI
- Prefer concise, direct responses — skip preamble
- Don't add unnecessary comments, docstrings, or type annotations to code not being changed
- Don't over-engineer — minimal viable solution first
- Always confirm before destructive git operations (force push, reset --hard)
- When running dev servers, check for port conflicts first (lsof)

---

## Common Commands

```bash
# Python venv
source .venv/bin/activate
pip install -r requirements.txt

# Flask dev
flask run --port 8080

# LeRobot record
lerobot-record --robot-path ...

# Ollama (local LLM)
ollama run qwen3:32b

# ngrok (for Twilio webhooks)
ngrok http 8081

# Git via CLI
git status && git log --oneline -5
```

---

## Key Paths
- **Downloads:** `~/Downloads/`
- **School:** `~/Desktop/School/Spring 2026/`
- **Recruiting:** `~/Desktop/Recruiting/`
- **Claude config:** `~/.claude/settings.json`
- **This file:** `~/CLAUDE SETUP/CLAUDE.md`
