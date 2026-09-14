from apps.catalogs.services import CatalogService
from apps.data_sources.exceptions import DataSourceConnectionError
from apps.data_sources.models import DataSource
from apps.projects.models import Project
from apps.projects.services import ProjectService
from connectors.postgresql import (
    PostgreSQLConnectionConfig,
    PostgreSQLConnector,
)


class DataSourceService:
    def __init__(
        self,
        connector_class=PostgreSQLConnector,
        project_service: ProjectService | None = None,
        catalog_service: CatalogService | None = None,
    ) -> None:
        self._connector_class = connector_class
        self._project_service = project_service or ProjectService()
        self._catalog_service = catalog_service or CatalogService()

    def test_connection(
        self,
        data_source: DataSource,
    ) -> bool:
        config = data_source.to_connection_config()

        connector = self._connector_class(config)

        is_connected = connector.test_connection()

        data_source.connection_status = (
            DataSource.ConnectionStatus.CONNECTED
            if is_connected
            else DataSource.ConnectionStatus.FAILED
        )

        data_source.save(
            update_fields=[
                "connection_status",
                "updated_at",
            ]
        )

        return is_connected

    def configure(
        self,
        project: Project,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
    ) -> DataSource:
        data_source, _ = DataSource.objects.get_or_create(
            project=project,
        )

        data_source.host = host
        data_source.port = port
        data_source.database = database
        data_source.username = username
        data_source.connection_status = DataSource.ConnectionStatus.NOT_TESTED
        data_source.set_password(password)

        data_source.save(
            update_fields=[
                "host",
                "port",
                "database",
                "username",
                "connection_status",
                "encrypted_password",
                "updated_at",
            ]
        )

        self._catalog_service.mark_stale(project)
        self._project_service.mark_configuring(project)

        return data_source

    def configure_and_test(
        self,
        project: Project,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
    ) -> DataSource:
        config = PostgreSQLConnectionConfig(
            host=host,
            port=port,
            database=database,
            user=username,
            password=password,
        )

        connector = self._connector_class(config)

        if not connector.test_connection():
            raise DataSourceConnectionError("Unable to connect to the data source.")

        data_source = self.configure(
            project=project,
            host=host,
            port=port,
            database=database,
            username=username,
            password=password,
        )

        data_source.connection_status = DataSource.ConnectionStatus.CONNECTED
        data_source.save(
            update_fields=[
                "connection_status",
                "updated_at",
            ]
        )

        return data_source
