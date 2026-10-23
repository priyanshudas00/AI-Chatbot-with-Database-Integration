from typing import Any, Dict, List, Optional

from src.db.database import DatabaseManager
from src.exceptions import DatabaseError


class ChatRepository:
    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def create_chat(self, user_name: str, topic: Optional[str]) -> int:
        query = "INSERT INTO chats (user_name, topic) VALUES (%s, %s)"
        try:
            with self.db_manager.get_connection() as connection:
                cursor = connection.cursor()
                cursor.execute(query, (user_name, topic))
                chat_id = cursor.lastrowid
                cursor.close()
                return chat_id
        except Exception as error:
            raise DatabaseError(f"Failed to create chat: {error}") from error

    def list_chats(self) -> List[Dict[str, Any]]:
        query = "SELECT id, user_name, topic, created_at FROM chats ORDER BY created_at DESC"
        try:
            with self.db_manager.get_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(query)
                rows = cursor.fetchall()
                cursor.close()
                return rows
        except Exception as error:
            raise DatabaseError(f"Failed to list chats: {error}") from error

    def update_chat_topic(self, chat_id: int, topic: str) -> bool:
        query = "UPDATE chats SET topic = %s WHERE id = %s"
        try:
            with self.db_manager.get_connection() as connection:
                cursor = connection.cursor()
                cursor.execute(query, (topic, chat_id))
                updated = cursor.rowcount > 0
                cursor.close()
                return updated
        except Exception as error:
            raise DatabaseError(f"Failed to update chat topic: {error}") from error

    def delete_chat(self, chat_id: int) -> bool:
        query = "DELETE FROM chats WHERE id = %s"
        try:
            with self.db_manager.get_connection() as connection:
                cursor = connection.cursor()
                cursor.execute(query, (chat_id,))
                deleted = cursor.rowcount > 0
                cursor.close()
                return deleted
        except Exception as error:
            raise DatabaseError(f"Failed to delete chat: {error}") from error


class MessageRepository:
    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def create_message(self, chat_id: int, role: str, content: str, token_count: Optional[int]) -> int:
        query = """
            INSERT INTO messages (chat_id, role, content, token_count)
            VALUES (%s, %s, %s, %s)
        """
        try:
            with self.db_manager.get_connection() as connection:
                cursor = connection.cursor()
                cursor.execute(query, (chat_id, role, content, token_count))
                message_id = cursor.lastrowid
                cursor.close()
                return message_id
        except Exception as error:
            raise DatabaseError(f"Failed to create message: {error}") from error

    def list_messages_by_chat(self, chat_id: int) -> List[Dict[str, Any]]:
        query = """
            SELECT id, chat_id, role, content, token_count, created_at
            FROM messages
            WHERE chat_id = %s
            ORDER BY created_at ASC
        """
        try:
            with self.db_manager.get_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(query, (chat_id,))
                rows = cursor.fetchall()
                cursor.close()
                return rows
        except Exception as error:
            raise DatabaseError(f"Failed to list messages: {error}") from error
    def delete_message(self, message_id: int) -> bool:
        query = "DELETE FROM messages WHERE id = %s"
        try:
            with self.db_manager.get_connection() as connection:
                cursor = connection.cursor()
                cursor.execute(query, (message_id,))
                deleted = cursor.rowcount > 0
                cursor.close()
                return deleted
        except Exception as error:
            raise DatabaseError(f"Failed to delete message: {error}") from error

