from unittest.mock import MagicMock

from backend.application.tools.sql_query import SQLQueryTool


def test_rejects_non_select():
    tool = SQLQueryTool(MagicMock())
    assert "Error" in tool.execute("DELETE FROM document")


def test_rejects_non_document_table():
    tool = SQLQueryTool(MagicMock())
    assert "Error" in tool.execute("SELECT * FROM users")


def test_rejects_drop():
    tool = SQLQueryTool(MagicMock())
    assert "Error" in tool.execute("SELECT 1; DROP TABLE document")
