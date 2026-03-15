import logging

from sqlmodel import Session, text

logger = logging.getLogger(__name__)

ALLOWED_TABLES = {"document"}
MAX_ROWS = 50


class SQLQueryTool:
    """Read-only SQL access to the Document table for aggregation queries."""

    def __init__(self, db_session: Session) -> None:
        self._session = db_session

    def execute(self, query: str) -> str:
        normalized = query.strip().lower()

        if not normalized.startswith("select"):
            return "Error: Only SELECT queries are allowed."

        for keyword in ("insert", "update", "delete", "drop", "alter", "create"):
            if keyword in normalized:
                return f"Error: {keyword.upper()} operations are not allowed."

        if "document" not in normalized:
            return "Error: Only queries against the 'document' table are allowed."

        try:
            if "limit" not in normalized:
                query = query.rstrip(";") + f" LIMIT {MAX_ROWS}"

            rows = self._session.exec(text(query)).all()
            if not rows:
                return "No results found."

            lines = [str(row) for row in rows[:MAX_ROWS]]
            return "\n".join(lines)
        except Exception as e:
            logger.warning("SQL query failed: %s", e)
            return f"Error executing query: {e}"
