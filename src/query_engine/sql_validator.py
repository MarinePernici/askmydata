from pglast import ast, parse_sql
from pglast.parser import ParseError
from pglast.visitors import Visitor

from query_engine.types import SQLValidationResult


class MutatingStatementVisitor(Visitor):
    """Detect data- or schema-modifying statements in a PostgreSQL AST."""

    def __init__(self) -> None:
        super().__init__()
        self.has_mutating_statement = False

    def visit_InsertStmt(self, ancestors, node):
        self.has_mutating_statement = True

    def visit_UpdateStmt(self, ancestors, node):
        self.has_mutating_statement = True

    def visit_DeleteStmt(self, ancestors, node):
        self.has_mutating_statement = True

    def visit_MergeStmt(self, ancestors, node):
        self.has_mutating_statement = True


class SQLValidator:
    """Validate generated SQL before execution."""

    def validate(self, sql: str) -> SQLValidationResult:
        if not sql.strip():
            return SQLValidationResult(
                is_valid=False,
                error="SQL query is empty.",
            )

        try:
            statements = parse_sql(sql)
        except ParseError:
            return SQLValidationResult(
                is_valid=False,
                error="SQL query has invalid PostgreSQL syntax.",
            )

        if len(statements) != 1:
            return SQLValidationResult(
                is_valid=False,
                error="Exactly one SQL statement is allowed.",
            )

        statement = statements[0].stmt

        if not isinstance(statement, ast.SelectStmt):
            return SQLValidationResult(
                is_valid=False,
                error="Only SELECT queries are allowed.",
            )

        visitor = MutatingStatementVisitor()
        visitor(statement)

        if visitor.has_mutating_statement:
            return SQLValidationResult(
                is_valid=False,
                error="Data-modifying operations are not allowed.",
            )

        return SQLValidationResult(is_valid=True)
