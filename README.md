# AI Chatbot with Database Integration

A Python web application that integrates an **AI agent API (OpenRouter)** with **MySQL** to store and retrieve chat history using full CRUD operations, plus SQL-based usage reports.

---

## Tech Stack

- **Python 3.10+**
- **Flask 3.0** (web framework / REST API)
- **MySQL** (via `mysql-connector-python`)
- **OpenRouter API** (via OpenAI SDK) — chat completions + embeddings
- **python-dotenv** (environment configuration)
- **Git / GitHub** (version control)

---

## Features

- OOP-based design using service and repository classes.
- Full CRUD for chats and message history.
- AI agent (OpenRouter) chat completions with conversation history.
- Embeddings endpoint.
- JSON request/response payloads over HTTP/HTTPS.
- Exception handling for API and database failures.
- Indexed MySQL schema for fast chat/message queries.
- SQL reporting with joins, filtering, sorting, and aggregate functions.
- HTML/CSS/JavaScript web interface for chat management and messaging.

---

## Project Structure

```
AI_Chatbot/
  .env
  .env.example
  README.md
  requirements.txt
  web_app.py
  sql/
    schema.sql
  src/
    __init__.py
    config.py
    exceptions.py
    db/
      __init__.py
      database.py
      chat_repository.py
    models/
      __init__.py
      entities.py
    services/
      __init__.py
      openrouter_client.py
      chatbot_service.py
      report_service.py
  static/
    app.js
    favicon.svg
    style.css
  templates/
    index.html
```

---

## Prerequisites

- Python 3.10 or newer (tested on 3.14)
- A MySQL server (local or cloud, e.g. Aiven)
- An OpenRouter account + API key

---

## Setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd AI_Chatbot
```

### 2. Create and activate a virtual environment

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

`requirements.txt`:

```
mysql-connector-python==9.0.0
python-dotenv==1.0.1
requests==2.32.5
Flask==3.0.3
openai>=2.26.0,<3.0.0
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and fill in values:

```bash
cp .env.example .env
```

`.env`:

```env
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_CHAT_MODEL=nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free
OPENROUTER_EMBEDDING_MODEL=nvidia/nemotron-3.5-embed-8b:free

MYSQL_HOST=your-mysql-host
MYSQL_PORT=3306
MYSQL_USER=your-mysql-user
MYSQL_PASSWORD=your-mysql-password
MYSQL_DATABASE=ai_chatbot
MYSQL_SSL_MODE=REQUIRED
MYSQL_SSL_CA=/path/to/ca.pem
```

#### API key source

- **OpenRouter API key**: create one at <https://openrouter.ai/keys>. Free models (suffix `:free`) are available; the default chat model is `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free`.
- **MySQL**: use a local MySQL instance or a managed provider (e.g. Aiven). Set `MYSQL_SSL_MODE=DISABLED` for local, `REQUIRED` for cloud, and provide `MYSQL_SSL_CA` if needed.

### 5. Create the database schema

Run the SQL file in MySQL:

```sql
SOURCE sql/schema.sql;
```

Or let the app create tables automatically on startup (`ensure_schema()` in `web_app.py`).

`sql/schema.sql`:

```sql
CREATE DATABASE IF NOT EXISTS ai_chatbot;
USE ai_chatbot;

CREATE TABLE IF NOT EXISTS chats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_name VARCHAR(100) NOT NULL,
    topic VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    chat_id INT NOT NULL,
    role ENUM('user', 'assistant') NOT NULL,
    content TEXT NOT NULL,
    token_count INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_messages_chat
        FOREIGN KEY (chat_id) REFERENCES chats(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_messages_chat_id ON messages(chat_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
```

### 6. Start the Flask server

```bash
python web_app.py
```

Open your browser at:

```
http://127.0.0.1:5000
```
---

## Configuration (`src/config.py`)

```python
import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=True)

@dataclass(frozen=True)
class Settings:
    openrouter_api_key: str
    openrouter_base_url: str
    openrouter_chat_model: str
    openrouter_embedding_model: str
    mysql_host: str
    mysql_port: int
    mysql_user: str
    mysql_password: str
    mysql_database: str
    mysql_ssl_mode: str
    mysql_ssl_ca: str

    @staticmethod
    def from_env() -> "Settings":
        return Settings(
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY", ""),
            openrouter_base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            openrouter_chat_model=os.getenv("OPENROUTER_CHAT_MODEL", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"),
            openrouter_embedding_model=os.getenv("OPENROUTER_EMBEDDING_MODEL", "nvidia/nemotron-3.5-embed-8b:free"),
            mysql_host=os.getenv("MYSQL_HOST", "localhost"),
            mysql_port=int(os.getenv("MYSQL_PORT", "3306")),
            mysql_user=os.getenv("MYSQL_USER", "root"),
            mysql_password=os.getenv("MYSQL_PASSWORD", ""),
            mysql_database=os.getenv("MYSQL_DATABASE", "ai_chatbot"),
            mysql_ssl_mode=os.getenv("MYSQL_SSL_MODE", "DISABLED"),
            mysql_ssl_ca=os.getenv("MYSQL_SSL_CA", ""),
        )
```

---

## REST API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/` | Web UI |
| GET | `/favicon.ico` | Favicon |
| GET | `/api/health/db` | Database health check |
| GET | `/api/chats` | List all chats |
| POST | `/api/chats` | Create a chat (`user_name`, optional `topic`) |
| GET | `/api/chats/<id>/messages` | List messages of a chat |
| POST | `/api/chats/<id>/messages` | Send a message, get AI reply |
| PATCH | `/api/chats/<id>` | Rename chat topic |
| DELETE | `/api/chats/<id>` | Delete a chat (cascades messages) |
| DELETE | `/api/messages/<id>` | Delete a single message |
| POST | `/api/embeddings` | Generate an embedding (`input`) |
| GET | `/api/reports/chat-summary` | Chat summary report (optional `user_name`) |
| GET | `/api/reports/top-users` | Top users by message count (optional `limit`) |

### Example: create chat

```bash
curl -X POST http://127.0.0.1:5000/api/chats \
  -H "Content-Type: application/json" \
  -d '{"user_name": "Alice", "topic": "General"}'
```

### Example: send message

```bash
curl -X POST http://127.0.0.1:5000/api/chats/1/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'
```

Response:

```json
{
  "chat_id": 1,
  "reply": "Hi! How can I help you today?",
  "token_count": 12
}
```

---

## Key Code

### AI client (`src/services/openrouter_client.py`)

```python
class OpenRouterClient:
    def __init__(self, settings: Settings) -> None:
        self.api_key = settings.openrouter_api_key
        self.base_url = settings.openrouter_base_url
        self.chat_model = settings.openrouter_chat_model
        self.embedding_model = settings.openrouter_embedding_model
        self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)

    def generate_reply(self, user_message, history=None):
        # builds system + history + user messages, calls chat.completions
        ...
        return reply, token_count
```

### Chat service (`src/services/chatbot_service.py`)

```python
class ChatbotService:
    def send_message(self, chat_id, user_text):
        history = self.message_repository.list_messages_by_chat(chat_id)
        self.message_repository.create_message(chat_id, "user", user_text, None)
        mapped_history = [...]
        bot_reply, token_count = self.llm_client.generate_reply(user_text, history=mapped_history)
        self.message_repository.create_message(chat_id, "assistant", bot_reply, token_count)
        return {"chat_id": chat_id, "reply": bot_reply, "token_count": token_count}
```

### Database manager with connection pooling (`src/db/database.py`)

```python
class DatabaseManager:
    def __init__(self, settings):
        self.settings = settings
        self._pool = None

    def _get_pool(self):
        if self._pool is None:
            self._pool = pooling.MySQLConnectionPool(
                pool_name="ai_chatbot_pool", pool_size=5, **self._build_config()
            )
        return self._pool

    @contextmanager
    def get_connection(self):
        connection = self._get_pool().get_connection()
        try:
            yield connection
            connection.commit()
        except Error as error:
            connection.rollback()
            raise DatabaseError(...) from error
        finally:
            if connection and connection.is_connected():
                connection.close()
```

---

## SQL Reporting Queries

### Chat Summary (Join + Aggregate + Sorting)

```sql
SELECT
  c.id AS chat_id,
  c.user_name,
  c.topic,
  COUNT(m.id) AS total_messages,
  SUM(CASE WHEN m.role = 'assistant' THEN COALESCE(m.token_count, 0) ELSE 0 END) AS total_assistant_tokens,
  MAX(m.created_at) AS last_activity_at
FROM chats c
LEFT JOIN messages m ON c.id = m.chat_id
GROUP BY c.id, c.user_name, c.topic
ORDER BY last_activity_at DESC, total_messages DESC;
```

### Top Users by Message Count (Filter + Aggregate)

```sql
SELECT
  c.user_name,
  COUNT(m.id) AS message_count
FROM chats c
INNER JOIN messages m ON c.id = m.chat_id
GROUP BY c.user_name
HAVING COUNT(m.id) > 0
ORDER BY message_count DESC, c.user_name ASC
LIMIT 5;
```

---

## Version Control Practices

### Push local code to GitHub (step-by-step)

1. **Prerequisites**
   - Git installed (https://git-scm.com)
   - GitHub account (https://github.com)

2. **Create a repository on GitHub**
   - Log in → **+** → **New repository**.
   - Set name, visibility (Public/Private), optional README/.gitignore/license.
   - Click **Create repository** and copy the remote URL.

3. **Initialize local repo**

   ```bash
   cd path/to/your/project
   git init
   ```

4. **Stage files**

   ```bash
   git add .
   # or specific files: git add file1.py file2.js
   ```

5. **Commit**

   ```bash
   git commit -m "Initial commit"
   ```

6. **Link remote**

   ```bash
   git remote add origin https://github.com/your-username/your-repo.git
   # SSH alternative:
   # git remote add origin git@github.com:your-username/your-repo.git
   ```

7. **Push**

   ```bash
   git push -u origin main
   # use 'master' if that is your default branch
   ```

   The `-u` flag sets upstream so future `git push`/`git pull` need no branch.

8. **Verify** — refresh the GitHub repo page to see files and history.

### Common tips / troubleshooting

| Situation | Fix |
|---|---|
| First push fails: "remote: Repository not found." | Double-check remote URL and authentication (PAT for HTTPS). |
| HTTPS auth error | Use a Personal Access Token: Settings → Developer settings → PATs. |
| SSH not set up | Follow GitHub SSH guide; use `git@github.com:...` URL. |
| Accidentally pushed wrong commit | Use `git reset` carefully or push a fixing commit. |
| Large/sensitive files | Use Git LFS or remove before committing. |

### Quick one-liner (repo already created on GitHub)

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/your-username/your-repo.git
git push -u origin main
```

---

## Troubleshooting

- **`Missing OPENROUTER_API_KEY`**: ensure `.env` exists and `OPENROUTER_API_KEY` is set.
- **DB connection errors**: verify `MYSQL_*` values, SSL mode, and that the schema is created.
- **Rate limits (429)**: free models have limits; wait or switch `OPENROUTER_CHAT_MODEL`.
- **Slow replies**: the default model is a reasoning model; reduce `max_tokens` or pick a faster model.

---

## License

MIT (or your preferred license).

