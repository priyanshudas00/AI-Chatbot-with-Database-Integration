from flask import Flask, jsonify, render_template, request

from src.config import Settings
from src.db.chat_repository import ChatRepository, MessageRepository
from src.db.database import DatabaseManager
from src.exceptions import ApiError, DatabaseError, RateLimitError
from src.services.chatbot_service import ChatbotService
from src.services.openrouter_client import OpenRouterClient
from src.services.report_service import ReportService


settings = Settings.from_env()
db_manager = DatabaseManager(settings)
chat_repository = ChatRepository(db_manager)
message_repository = MessageRepository(db_manager)
llm_client = OpenRouterClient(settings)
chatbot_service = ChatbotService(
    chat_repository=chat_repository,
    message_repository=message_repository,
    llm_client=llm_client,
)
report_service = ReportService(db_manager)

app = Flask(__name__)


def ensure_schema() -> None:
    statements = [
        """
        CREATE TABLE IF NOT EXISTS chats (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_name VARCHAR(100) NOT NULL,
            topic VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
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
        )
        """,
        "CREATE INDEX idx_messages_chat_id ON messages(chat_id)",
        "CREATE INDEX idx_messages_created_at ON messages(created_at)",
    ]

    with db_manager.get_connection() as connection:
        cursor = connection.cursor()
        for statement in statements:
            try:
                cursor.execute(statement)
            except Exception as error:
                # Duplicate index creation should not block app startup.
                if "Duplicate key name" not in str(error):
                    raise
        cursor.close()


ensure_schema()


@app.route("/")
def home() -> str:
    return render_template("index.html")


@app.route("/favicon.ico")
def favicon():
    return "", 204


@app.route("/api/health/db", methods=["GET"])
def db_health():
    try:
        with db_manager.get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
        return jsonify({"status": "ok"})
    except DatabaseError as error:
        return jsonify({"status": "error", "error": str(error)}), 500


@app.route("/api/chats", methods=["GET"])
def list_chats():
    try:
        return jsonify(chat_repository.list_chats())
    except DatabaseError as error:
        return jsonify({"error": str(error)}), 500


@app.route("/api/chats", methods=["POST"])
def create_chat():
    payload = request.get_json(silent=True) or {}
    user_name = (payload.get("user_name") or "").strip()
    topic = (payload.get("topic") or "").strip() or None

    if not user_name:
        return jsonify({"error": "user_name is required"}), 400

    try:
        chat_id = chatbot_service.start_chat(user_name, topic)
        return jsonify({"chat_id": chat_id}), 201
    except DatabaseError as error:
        return jsonify({"error": str(error)}), 500


@app.route("/api/chats/<int:chat_id>/messages", methods=["GET"])
def get_messages(chat_id: int):
    try:
        return jsonify(chatbot_service.get_chat_history(chat_id))
    except DatabaseError as error:
        return jsonify({"error": str(error)}), 500


@app.route("/api/chats/<int:chat_id>/messages", methods=["POST"])
def send_message(chat_id: int):
    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip()

    if not message:
        return jsonify({"error": "message is required"}), 400

    try:
        result = chatbot_service.send_message(chat_id, message)
        return jsonify(result)
    except RateLimitError as error:
        return jsonify({"error": str(error)}), 429
    except ApiError as error:
        return jsonify({"error": str(error)}), 400
    except DatabaseError as error:
        return jsonify({"error": str(error)}), 500


@app.route("/api/chats/<int:chat_id>", methods=["PATCH"])
def update_chat(chat_id: int):
    payload = request.get_json(silent=True) or {}
    topic = (payload.get("topic") or "").strip()

    if not topic:
        return jsonify({"error": "topic is required"}), 400

    try:
        updated = chatbot_service.rename_chat_topic(chat_id, topic)
        return jsonify({"updated": updated})
    except DatabaseError as error:
        return jsonify({"error": str(error)}), 500


@app.route("/api/chats/<int:chat_id>", methods=["DELETE"])
def delete_chat(chat_id: int):
    try:
        deleted = chatbot_service.delete_chat(chat_id)
        return jsonify({"deleted": deleted})
    except DatabaseError as error:
        return jsonify({"error": str(error)}), 500


@app.route("/api/reports/chat-summary", methods=["GET"])
def chat_summary_report():
    user_name = (request.args.get("user_name") or "").strip() or None
    try:
        return jsonify(report_service.chat_summary(user_name))
    except DatabaseError as error:
        return jsonify({"error": str(error)}), 500


@app.route("/api/reports/top-users", methods=["GET"])
def top_users_report():
    try:
        limit = int(request.args.get("limit", 5))
    except (TypeError, ValueError):
        return jsonify({"error": "limit must be an integer"}), 400
    try:
        return jsonify(report_service.top_users_by_message_count(limit))
    except DatabaseError as error:
        return jsonify({"error": str(error)}), 500


@app.route("/api/messages/<int:message_id>", methods=["DELETE"])
def delete_message(message_id: int):
    try:
        deleted = message_repository.delete_message(message_id)
        return jsonify({"deleted": deleted})
    except DatabaseError as error:
        return jsonify({"error": str(error)}), 500


@app.route("/api/embeddings", methods=["POST"])
def create_embedding():
    payload = request.get_json(silent=True) or {}
    text = (payload.get("input") or "").strip()

    if not text:
        return jsonify({"error": "input is required"}), 400

    try:
        result = llm_client.generate_embedding(text)
        return jsonify(result)
    except RateLimitError as error:
        return jsonify({"error": str(error)}), 429
    except ApiError as error:
        return jsonify({"error": str(error)}), 400


if __name__ == "__main__":
    app.run(debug=True)
