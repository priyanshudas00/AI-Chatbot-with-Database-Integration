from typing import Any, Dict, List, Optional

from src.db.chat_repository import ChatRepository, MessageRepository


class ChatbotService:
    def __init__(
        self,
        chat_repository: ChatRepository,
        message_repository: MessageRepository,
        llm_client: Any,
    ) -> None:
        self.chat_repository = chat_repository
        self.message_repository = message_repository
        self.llm_client = llm_client

    def start_chat(self, user_name: str, topic: Optional[str]) -> int:
        return self.chat_repository.create_chat(user_name, topic)

    def send_message(self, chat_id: int, user_text: str) -> Dict[str, Any]:
        history = self.message_repository.list_messages_by_chat(chat_id)
        self.message_repository.create_message(chat_id, "user", user_text, None)
        mapped_history = [
            {"role": item.get("role", "user"), "content": item.get("content", "")}
            for item in history
            if item.get("content")
        ]
        bot_reply, token_count = self.llm_client.generate_reply(
            user_text, history=mapped_history
        )
        self.message_repository.create_message(chat_id, "assistant", bot_reply, token_count)
        return {
            "chat_id": chat_id,
            "reply": bot_reply,
            "token_count": token_count,
        }

    def get_chat_history(self, chat_id: int) -> List[Dict[str, Any]]:
        return self.message_repository.list_messages_by_chat(chat_id)

    def rename_chat_topic(self, chat_id: int, topic: str) -> bool:
        return self.chat_repository.update_chat_topic(chat_id, topic)

    def delete_chat(self, chat_id: int) -> bool:
        return self.chat_repository.delete_chat(chat_id)
