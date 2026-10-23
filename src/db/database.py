from contextlib import contextmanager

from mysql.connector import Error
from mysql.connector import pooling

from src.config import Settings
from src.exceptions import DatabaseError


class DatabaseManager:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._pool = None

    def _build_config(self) -> dict:
        config = {
            "host": self.settings.mysql_host,
            "port": self.settings.mysql_port,
            "user": self.settings.mysql_user,
            "password": self.settings.mysql_password,
            "database": self.settings.mysql_database,
            "pool_reset_session": True,
        }
        ssl_mode = (self.settings.mysql_ssl_mode or "").strip().upper()
        if ssl_mode and ssl_mode != "DISABLED":
            config["ssl_disabled"] = False
            if self.settings.mysql_ssl_ca:
                config["ssl_ca"] = self.settings.mysql_ssl_ca
        return config

    def _get_pool(self):
        if self._pool is None:
            self._pool = pooling.MySQLConnectionPool(
                pool_name="ai_chatbot_pool",
                pool_size=5,
                **self._build_config(),
            )
        return self._pool

    @contextmanager
    def get_connection(self):
        connection = None
        try:
            connection = self._get_pool().get_connection()
            yield connection
            connection.commit()
        except Error as error:
            if connection:
                connection.rollback()
            raise DatabaseError(f"Database connection/transaction error: {error}") from error
        finally:
            if connection and connection.is_connected():
                connection.close()
