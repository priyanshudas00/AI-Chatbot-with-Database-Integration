from datetime import datetime
from typing import Any, Dict, List, Optional

from src.db.database import DatabaseManager
from src.exceptions import DatabaseError


class ReportService:
    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def chat_summary(self, user_name: Optional[str] = None) -> List[Dict[str, Any]]:
        query = """
            SELECT
                c.id AS chat_id,
                c.user_name,
                c.topic,
                COUNT(m.id) AS total_messages,
                SUM(CASE WHEN m.role = 'assistant' THEN COALESCE(m.token_count, 0) ELSE 0 END) AS total_assistant_tokens,
                MAX(m.created_at) AS last_activity_at
            FROM chats c
            LEFT JOIN messages m ON c.id = m.chat_id
            WHERE (%s IS NULL OR c.user_name = %s)
            GROUP BY c.id, c.user_name, c.topic
            ORDER BY last_activity_at DESC, total_messages DESC
        """
        try:
            with self.db_manager.get_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(query, (user_name, user_name))
                rows = cursor.fetchall()
                cursor.close()
                return rows
        except Exception as error:
            raise DatabaseError(f"Failed to generate chat summary report: {error}") from error

    def messages_in_range(self, start_at: datetime, end_at: datetime) -> List[Dict[str, Any]]:
        query = """
            SELECT
                m.id,
                m.chat_id,
                c.user_name,
                c.topic,
                m.role,
                m.content,
                m.token_count,
                m.created_at
            FROM messages m
            INNER JOIN chats c ON m.chat_id = c.id
            WHERE m.created_at BETWEEN %s AND %s
            ORDER BY m.created_at ASC
        """
        try:
            with self.db_manager.get_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(query, (start_at, end_at))
                rows = cursor.fetchall()
                cursor.close()
                return rows
        except Exception as error:
            raise DatabaseError(f"Failed to fetch messages by range: {error}") from error

    def top_users_by_message_count(self, limit: int = 5) -> List[Dict[str, Any]]:
        query = """
            SELECT
                c.user_name,
                COUNT(m.id) AS message_count
            FROM chats c
            INNER JOIN messages m ON c.id = m.chat_id
            GROUP BY c.user_name
            HAVING COUNT(m.id) > 0
            ORDER BY message_count DESC, c.user_name ASC
            LIMIT %s
        """
        try:
            with self.db_manager.get_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(query, (limit,))
                rows = cursor.fetchall()
                cursor.close()
                return rows
        except Exception as error:
            raise DatabaseError(f"Failed to generate top users report: {error}") from error
