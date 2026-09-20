from pglast import ast, parse_sql
from pglast.parser import ParseError
from pglast.visitors import Visitor

from catalog.types import KnowledgeCatalog
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


class CTENameVisitor(Visitor):
    """Collect CTE names declared by a PostgreSQL query."""

    def __init__(self) -> None:
        super().__init__()
        self.names: set[str] = set()

    def visit_CommonTableExpr(self, ancestors, node):
        self.names.add(node.ctename)


class ReferencedTableVisitor(Visitor):
    """Collect physical tables referenced by a PostgreSQL query."""

    def __init__(self, cte_names: set[str]) -> None:
        super().__init__()
        self._cte_names = cte_names
        self.tables: set[tuple[str | None, str]] = set()

    def visit_RangeVar(self, ancestors, node):
        if node.schemaname is None and node.relname in self._cte_names:
            return

        self.tables.add((node.schemaname, node.relname))


class SQLValidator:
    """Validate generated SQL before execution."""

    def validate(
        self,
        sql: str,
        catalog: KnowledgeCatalog | None = None,
    ) -> SQLValidationResult:
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

        if catalog is not None:
            cte_visitor = CTENameVisitor()
            cte_visitor(statement)

            table_visitor = ReferencedTableVisitor(cte_visitor.names)
            table_visitor(statement)

            allowed_tables = {(table.schema, table.name) for table in catalog.tables}

            if any(table not in allowed_tables for table in table_visitor.tables):
                return SQLValidationResult(
                    is_valid=False,
                    error="SQL query references a table outside the catalog scope.",
                )

        return SQLValidationResult(is_valid=True)
