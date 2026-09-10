from apps.data_sources.models import DataSource
from connectors.postgresql import PostgreSQLConnector


class DataSourceService:
    def __init__(
        self,
        connector_class=PostgreSQLConnector,
    ) -> None:
        self._connector_class = connector_class

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