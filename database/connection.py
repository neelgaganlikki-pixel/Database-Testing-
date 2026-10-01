import time
from typing import Any, Dict, List, Optional, Tuple, Union
import mysql.connector
from mysql.connector import Error, MySQLConnection
from mysql.connector.cursor import MySQLCursorDict

from config.db_config import get_db_config, get_server_config
from utils.logger import logger

class DatabaseManager:
    """Manages MySQL database connections and operations safely."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or get_db_config()
        self._connection: Optional[MySQLConnection] = None

    def connect(self) -> MySQLConnection:
        """Creates and returns a MySQL database connection."""
        try:
            if self._connection is None or not self._connection.is_connected():
                self._connection = mysql.connector.connect(**self.config)
                logger.debug("Database connection established successfully.")
            return self._connection
        except Error as e:
            logger.error(f"Failed to connect to MySQL database: {e}")
            raise

    def close(self) -> None:
        """Closes the current database connection if open."""
        if self._connection and self._connection.is_connected():
            try:
                self._connection.close()
                logger.debug("Database connection closed.")
            except Error as e:
                logger.warning(f"Error while closing connection: {e}")
            finally:
                self._connection = None

    def __enter__(self) -> "DatabaseManager":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        self.close()

    def commit(self) -> None:
        """Commits the active transaction."""
        if self._connection and self._connection.is_connected():
            self._connection.commit()
            logger.debug("Transaction committed.")

    def rollback(self) -> None:
        """Rolls back the active transaction."""
        if self._connection and self._connection.is_connected():
            self._connection.rollback()
            logger.debug("Transaction rolled back.")

    def begin_transaction(self) -> None:
        """Explicitly begins a transaction by disabling autocommit."""
        conn = self.connect()
        conn.autocommit = False
        logger.debug("Explicit transaction started.")

    def execute_query(self, query: str, params: Optional[Union[Tuple, Dict, List]] = None) -> int:
        """Executes a non-select query and returns affected rows count."""
        start_time = time.perf_counter()
        conn = self.connect()
        cursor = conn.cursor()
        try:
            logger.debug(f"Executing query: {query} with params: {params}")
            cursor.execute(query, params or ())
            affected = cursor.rowcount
            elapsed = (time.perf_counter() - start_time) * 1000
            logger.debug(f"Query executed in {elapsed:.2f}ms. Affected rows: {affected}")
            return affected
        except Error as e:
            logger.error(f"SQL execution error for query [{query}]: {e}")
            raise
        finally:
            cursor.close()

    def execute_select(
        self, query: str, params: Optional[Union[Tuple, Dict, List]] = None, dictionary: bool = True
    ) -> List[Dict[str, Any]]:
        """Executes a SELECT query and returns all matching records as dictionaries."""
        start_time = time.perf_counter()
        conn = self.connect()
        cursor = conn.cursor(dictionary=dictionary)
        try:
            logger.debug(f"Executing SELECT: {query} with params: {params}")
            cursor.execute(query, params or ())
            rows = cursor.fetchall()
            elapsed = (time.perf_counter() - start_time) * 1000
            logger.debug(f"SELECT completed in {elapsed:.2f}ms. Returned {len(rows)} records.")
            return rows
        except Error as e:
            logger.error(f"SQL SELECT error for query [{query}]: {e}")
            raise
        finally:
            cursor.close()

    def fetch_one(
        self, query: str, params: Optional[Union[Tuple, Dict, List]] = None, dictionary: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Executes a SELECT query and returns the first row or None."""
        start_time = time.perf_counter()
        conn = self.connect()
        cursor = conn.cursor(dictionary=dictionary)
        try:
            logger.debug(f"Executing fetch_one: {query} with params: {params}")
            cursor.execute(query, params or ())
            row = cursor.fetchone()
            elapsed = (time.perf_counter() - start_time) * 1000
            logger.debug(f"fetch_one completed in {elapsed:.2f}ms.")
            return row
        except Error as e:
            logger.error(f"SQL fetch_one error for query [{query}]: {e}")
            raise
        finally:
            cursor.close()

    def fetch_all(
        self, query: str, params: Optional[Union[Tuple, Dict, List]] = None, dictionary: bool = True
    ) -> List[Dict[str, Any]]:
        """Convenience alias for execute_select."""
        return self.execute_select(query, params, dictionary=dictionary)

    def execute_insert(self, query: str, params: Optional[Union[Tuple, Dict, List]] = None) -> int:
        """Executes an INSERT statement and returns the newly generated lastrowid."""
        start_time = time.perf_counter()
        conn = self.connect()
        cursor = conn.cursor()
        try:
            logger.debug(f"Executing INSERT: {query} with params: {params}")
            cursor.execute(query, params or ())
            inserted_id = cursor.lastrowid
            conn.commit()
            elapsed = (time.perf_counter() - start_time) * 1000
            logger.info(f"INSERT executed in {elapsed:.2f}ms. New ID: {inserted_id}")
            return inserted_id
        except Error as e:
            conn.rollback()
            logger.error(f"SQL INSERT error for query [{query}]: {e}")
            raise
        finally:
            cursor.close()

    def execute_update(self, query: str, params: Optional[Union[Tuple, Dict, List]] = None) -> int:
        """Executes an UPDATE statement, commits, and returns affected rows."""
        start_time = time.perf_counter()
        conn = self.connect()
        cursor = conn.cursor()
        try:
            logger.debug(f"Executing UPDATE: {query} with params: {params}")
            cursor.execute(query, params or ())
            affected = cursor.rowcount
            conn.commit()
            elapsed = (time.perf_counter() - start_time) * 1000
            logger.info(f"UPDATE executed in {elapsed:.2f}ms. Affected rows: {affected}")
            return affected
        except Error as e:
            conn.rollback()
            logger.error(f"SQL UPDATE error for query [{query}]: {e}")
            raise
        finally:
            cursor.close()

    def execute_delete(self, query: str, params: Optional[Union[Tuple, Dict, List]] = None) -> int:
        """Executes a DELETE statement, commits, and returns affected rows."""
        start_time = time.perf_counter()
        conn = self.connect()
        cursor = conn.cursor()
        try:
            logger.debug(f"Executing DELETE: {query} with params: {params}")
            cursor.execute(query, params or ())
            affected = cursor.rowcount
            conn.commit()
            elapsed = (time.perf_counter() - start_time) * 1000
            logger.info(f"DELETE executed in {elapsed:.2f}ms. Affected rows: {affected}")
            return affected
        except Error as e:
            conn.rollback()
            logger.error(f"SQL DELETE error for query [{query}]: {e}")
            raise
        finally:
            cursor.close()


# Module-level convenience functions required by framework specification
def create_connection(config: Optional[Dict[str, Any]] = None) -> MySQLConnection:
    """Creates a new database connection."""
    cfg = config or get_db_config()
    return mysql.connector.connect(**cfg)

def close_connection(connection: MySQLConnection) -> None:
    """Closes a database connection safely."""
    if connection and connection.is_connected():
        connection.close()

def execute_query(query: str, params: Optional[Union[Tuple, Dict]] = None) -> int:
    with DatabaseManager() as db:
        return db.execute_query(query, params)

def execute_select(query: str, params: Optional[Union[Tuple, Dict]] = None) -> List[Dict[str, Any]]:
    with DatabaseManager() as db:
        return db.execute_select(query, params)

def execute_insert(query: str, params: Optional[Union[Tuple, Dict]] = None) -> int:
    with DatabaseManager() as db:
        return db.execute_insert(query, params)

def execute_update(query: str, params: Optional[Union[Tuple, Dict]] = None) -> int:
    with DatabaseManager() as db:
        return db.execute_update(query, params)

def execute_delete(query: str, params: Optional[Union[Tuple, Dict]] = None) -> int:
    with DatabaseManager() as db:
        return db.execute_delete(query, params)

def fetch_one(query: str, params: Optional[Union[Tuple, Dict]] = None) -> Optional[Dict[str, Any]]:
    with DatabaseManager() as db:
        return db.fetch_one(query, params)

def fetch_all(query: str, params: Optional[Union[Tuple, Dict]] = None) -> List[Dict[str, Any]]:
    with DatabaseManager() as db:
        return db.fetch_all(query, params)

def commit(connection: MySQLConnection) -> None:
    if connection and connection.is_connected():
        connection.commit()

def rollback(connection: MySQLConnection) -> None:
    if connection and connection.is_connected():
        connection.rollback()

def begin_transaction(connection: MySQLConnection) -> None:
    if connection and connection.is_connected():
        connection.autocommit = False
