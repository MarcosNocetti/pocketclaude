# telegram-pc-bot

> Acesse o Claude Code pelo seu celular via Telegram — com autenticação 2FA, sessões persistentes e transferência de arquivos.

> Access Claude Code from your phone via Telegram — with 2FA authentication, persistent sessions, and file transfer.

---

## 🇧🇷 Português

### O que é

Um bot Telegram que roda localmente na sua máquina e encaminha suas mensagens para o **Claude Code** (CLI). Você interage com seu ambiente de desenvolvimento de qualquer lugar, pelo celular.

### Como funciona

```
[Celular] → Telegram → Bot Python → claude -p → Claude Code CLI
                           ↑                           ↓
                       TOTP 2FA          resposta JSON → Telegram
```

Veja o [diagrama completo](docs/architecture.md).

### Pré-requisitos

- Python 3.10+
- [Claude Code CLI](https://claude.ai/code) instalado e autenticado
- Conta no Telegram + bot criado via [@BotFather](https://t.me/botfather)
- Seu Telegram User ID (obtenha no [@userinfobot](https://t.me/userinfobot))

### Instalação

```bash
git clone https://github.com/SEU_USUARIO/telegram-pc-bot.git
cd telegram-pc-bot
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### Configuração

Edite o `.env`:

```bash
TELEGRAM_BOT_TOKEN=seu_token_aqui
TELEGRAM_ALLOWED_USER_ID=seu_user_id
TOTP_SECRET=gere_com_pyotp
CLAUDE_BIN=claude
UPLOAD_DIR=~/uploads
```

Gere o `TOTP_SECRET` e configure no seu app autenticador (Google Authenticator, Authy):

```bash
python3 -c "import pyotp; s = pyotp.random_base32(); print(s); print(pyotp.TOTP(s).provisioning_uri('telegram-pc-bot'))"
```

### Iniciando

```bash
python3 bot.py
```

### Comandos

| Comando | Descrição |
|---|---|
| `/login <código>` | Autentica via TOTP (obrigatório ao iniciar) |
| `/logout` | Encerra a sessão |
| `/new <nome> [dir]` | Cria nova sessão Claude no diretório especificado |
| `/attach <nome>` | Ativa uma sessão existente |
| `/sessions` | Lista sessões abertas |
| `/kill <nome>` | Encerra uma sessão |
| `/status` | Sessão ativa + uptime |
| `/send <caminho>` | Envia arquivo do PC para o Telegram |
| `/ls [caminho]` | Lista arquivos de um diretório |
| `/messages` | Lista mensagens na fila |
| `/rmq <n>\|all` | Remove mensagem(ns) da fila |
| _(qualquer texto)_ | Encaminha ao Claude Code na sessão ativa |

### Como adaptar para seu uso

- **Outro binário de IA:** troque `CLAUDE_BIN` por qualquer CLI que aceite `-p "mensagem"` e retorne JSON
- **Múltiplos usuários:** `TELEGRAM_ALLOWED_USER_ID` suporta apenas um ID — pull requests são bem-vindos
- **Serviço no boot:** no Linux, crie um serviço systemd apontando para `python3 bot.py`

### Segurança

- Apenas um `TELEGRAM_ALLOWED_USER_ID` é aceito
- Todo comando requer sessão TOTP ativa (TTL padrão: 8h)
- Token e segredo TOTP ficam apenas no `.env` — nunca no código

---

## 🇺🇸 English

### What is it

A Telegram bot that runs locally on your machine and forwards your messages to **Claude Code** (CLI). Interact with your development environment from anywhere, from your phone.

### How it works

```
[Phone] → Telegram → Python Bot → claude -p → Claude Code CLI
                         ↑                          ↓
                     TOTP 2FA         JSON response → Telegram
```

See the [full diagram](docs/architecture.md).

### Prerequisites

- Python 3.10+
- [Claude Code CLI](https://claude.ai/code) installed and authenticated
- Telegram account + bot created via [@BotFather](https://t.me/botfather)
- Your Telegram User ID (get it from [@userinfobot](https://t.me/userinfobot))

### Installation

```bash
git clone https://github.com/YOUR_USERNAME/telegram-pc-bot.git
cd telegram-pc-bot
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### Configuration

Edit `.env`:

```bash
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_ALLOWED_USER_ID=your_user_id
TOTP_SECRET=generate_with_pyotp
CLAUDE_BIN=claude
UPLOAD_DIR=~/uploads
```

Generate `TOTP_SECRET` and add to your authenticator app (Google Authenticator, Authy):

```bash
python3 -c "import pyotp; s = pyotp.random_base32(); print(s); print(pyotp.TOTP(s).provisioning_uri('telegram-pc-bot'))"
```

### Starting

```bash
python3 bot.py
```

### Commands

| Command | Description |
|---|---|
| `/login <code>` | Authenticate via TOTP (required on start) |
| `/logout` | End session |
| `/new <name> [dir]` | Create new Claude session in specified directory |
| `/attach <name>` | Activate an existing session |
| `/sessions` | List open sessions |
| `/kill <name>` | Close a session |
| `/status` | Active session + uptime |
| `/send <path>` | Send file from PC to Telegram |
| `/ls [path]` | List directory contents |
| `/messages` | List queued messages |
| `/rmq <n>\|all` | Remove message(s) from queue |
| _(any text)_ | Forward to Claude Code in active session |

### How to adapt for your use

- **Different AI binary:** replace `CLAUDE_BIN` with any CLI that accepts `-p "message"` and returns JSON
- **Multiple users:** `TELEGRAM_ALLOWED_USER_ID` supports only one ID — pull requests welcome
- **Boot service:** on Linux, create a systemd service pointing to `python3 bot.py`

### Security

- Only one `TELEGRAM_ALLOWED_USER_ID` is accepted — all others are silently ignored
- Every command requires an active TOTP session (default TTL: 8h)
- Token and TOTP secret stay in `.env` only — never in source code

---

## License

MIT
