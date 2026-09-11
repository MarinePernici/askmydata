class DataSourceNotConfiguredError(Exception):
    """Raised when a project has no configured data source."""


class CatalogScopeNotConfiguredError(Exception):
    """Raised when a project has no catalog scope."""