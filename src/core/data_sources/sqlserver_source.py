"""SQL Server数据源策略实现

该类实现了SQL Server数据源接口，支持：
- 数据加载
- SQL查询执行
- 元数据获取
- 上下文信息返回
"""

from typing import Any, Dict, List, Optional
import pandas as pd
from sqlalchemy import create_engine, text
from .base import DataSourceStrategy
from src.config.settings import get_config


class SQLServerDataSource(DataSourceStrategy):
    """SQL Server数据源策略实现"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 1433,
        database: str = "master",
        user: str = "sa",
        password: str = "",
        driver: str = "ODBC Driver 17 for SQL Server",
        schema: str = "dbo",
        connection_params: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化SQL Server数据源
        """
        config = get_config()
        mssql_config = config.data_source.sqlserver

        # Priority: explicit args > config > defaults
        self.host = (
            host if host != "localhost" else (mssql_config.host or "localhost")
        )
        # Handle port conversion safely
        config_port = mssql_config.port
        if isinstance(config_port, str) and config_port.isdigit():
            config_port = int(config_port)
        elif isinstance(config_port, str):
            config_port = 1433
        
        self.port = port if port != 1433 else (config_port or 1433)
        self.database = (
            database
            if database != "master"
            else (mssql_config.database or "master")
        )
        self.user = (
            user if user != "sa" else (mssql_config.user or "sa")
        )
        self.password = (
            password
            if password != ""
            else (mssql_config.password or "")
        )
        self.driver = (
            driver 
            if driver != "ODBC Driver 17 for SQL Server" 
            else (mssql_config.driver or "ODBC Driver 17 for SQL Server")
        )
        self.schema = schema if schema != "dbo" else (mssql_config.schema or "dbo")
        self.connection_params = connection_params or {}

        self._engine = None
        self._connection = None

    def _get_connection_string(self) -> str:
        """构建SQL Server连接字符串
        
        Format: mssql+pyodbc://user:password@host:port/database?driver=Driver+Name
        """
        # 对密码进行URL编码，防止特殊字符导致连接失败
        from urllib.parse import quote_plus
        encoded_password = quote_plus(self.password)
        
        base_url = f"mssql+pyodbc://{self.user}:{encoded_password}@{self.host}:{self.port}/{self.database}"
        return base_url

    def _get_engine(self):
        """获取SQLAlchemy engine"""
        if self._engine is None:
            try:
                from sqlalchemy import create_engine

                connection_string = self._get_connection_string()
                
                # 必须指定driver
                driver_param = f"driver={self.driver}"
                if "?" in connection_string:
                    connection_string += f"&{driver_param}"
                else:
                    connection_string += f"?{driver_param}"

                # 添加额外的连接参数
                if self.connection_params:
                    params = "&".join(
                        [f"{k}={v}" for k, v in self.connection_params.items()]
                    )
                    connection_string += f"&{params}"

                self._engine = create_engine(connection_string)

            except ImportError:
                raise ImportError(
                    "sqlalchemy and pyodbc are required for SQL Server data source. "
                    "Install them with: pip install sqlalchemy pyodbc"
                )

        return self._engine

    def load_data(self, table_name: str, limit: Optional[int] = None) -> pd.DataFrame:
        """
        从SQL Server表加载数据到DataFrame

        Args:
            table_name: 表名
            limit: 限制行数

        Returns:
            包含表数据的DataFrame
        """
        engine = self._get_engine()

        try:
            from sqlalchemy import text

            with engine.connect() as conn:
                # SQL Server使用TOP而不是LIMIT
                if limit:
                    query = text(
                        f"SELECT TOP {limit} * FROM {self.schema}.{table_name}"
                    )
                else:
                    query = text(f"SELECT * FROM {self.schema}.{table_name}")

                result = conn.execute(query)
                columns = [desc[0] for desc in result.cursor.description]
                rows = result.fetchall()
                df = pd.DataFrame(rows, columns=columns)

            return df

        except Exception as e:
            raise Exception(f"Failed to load data from table {table_name}: {str(e)}")

    def get_metadata(self) -> Dict[str, Any]:
        """
        返回数据源元数据

        Returns:
            包含元数据的字典
        """
        return {
            "source_type": "sqlserver",
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "schema": self.schema,
            "user": self.user,
            "tables": [], # 这里可以优化为动态获取
        }

    def get_context(self) -> Dict[str, str]:
        """
        返回业务逻辑和上下文信息

        Returns:
            包含上下文信息的字典
        """
        engine = self._get_engine()

        context = {
            "data_source_type": "sqlserver",
            "database": self.database,
            "schema": self.schema,
            "tables": {},
        }

        # 获取表信息
        try:
            from sqlalchemy import text

            with engine.connect() as conn:
                # SQL Server获取表名
                tables_query = text(
                    """
                    SELECT TABLE_NAME 
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_TYPE = 'BASE TABLE' 
                    AND TABLE_SCHEMA = :schema
                    ORDER BY TABLE_NAME
                """
                )

                tables = conn.execute(tables_query, {"schema": self.schema})
                context["tables"] = {row[0]: {"name": row[0]} for row in tables}

        except Exception as e:
            context["error"] = f"Failed to get context: {str(e)}"

        return context

    def execute_query(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        执行SQL查询

        Args:
            query: SQL查询语句
            params: 查询参数

        Returns:
            包含查询结果的DataFrame
        """
        engine = self._get_engine()

        try:
            from sqlalchemy import text

            with engine.connect() as conn:
                result = conn.execute(text(query), params or {})
                if result.cursor:
                    columns = [desc[0] for desc in result.cursor.description]
                    rows = result.fetchall()
                    df = pd.DataFrame(rows, columns=columns)
                else:
                    # 对于非查询语句（如INSERT/UPDATE），可能没有结果集
                    df = pd.DataFrame()

            return df

        except Exception as e:
            raise Exception(f"Failed to execute query: {str(e)}\nQuery: {query}")

    def get_schema_info(self, table_names: List[str]) -> str:
        """
        获取指定表的schema信息

        Args:
            table_names: 表名列表

        Returns:
            包含schema信息的字符串
        """
        engine = self._get_engine()
        schema_info = []

        from sqlalchemy import text

        def _quote_ident(name: str) -> str:
            return "[" + name.replace("]", "]]" ) + "]"

        def _format_samples(values: List[Any], max_len: int = 50) -> str:
            if not values:
                return "N/A"
            formatted = []
            for v in values:
                if isinstance(v, str):
                    v = v.strip()
                    if len(v) > max_len:
                        v = v[: max_len - 3] + "..."
                    formatted.append(f"'{v}'")
                else:
                    formatted.append(str(v))
            return ", ".join(formatted)

        try:
            with engine.connect() as conn:
                for table_name in table_names:
                    # 获取表结构
                    columns_query = text(
                        """
                        SELECT 
                            COLUMN_NAME,
                            DATA_TYPE,
                            CHARACTER_MAXIMUM_LENGTH,
                            IS_NULLABLE
                        FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_NAME = :table_name
                            AND TABLE_SCHEMA = :schema
                        ORDER BY ORDINAL_POSITION
                    """
                    )

                    columns = list(
                        conn.execute(
                            columns_query,
                            {"table_name": table_name, "schema": self.schema},
                        )
                    )

                    schema_info.append(f"\n=== Table: {table_name} ===\n")

                    for col in columns:
                        column_name = col[0]
                        sample_values: List[Any] = []
                        try:
                            sample_query = text(
                                f"""
                                SELECT DISTINCT TOP (3) {_quote_ident(column_name)}
                                FROM {_quote_ident(self.schema)}.{_quote_ident(table_name)}
                                WHERE {_quote_ident(column_name)} IS NOT NULL
                                """
                            )
                            sample_values = [row[0] for row in conn.execute(sample_query)]
                        except Exception:
                            sample_values = []

                        schema_info.append(
                            f"{column_name:<30} {col[1]} "
                            f"(max length: {col[2] or 'N/A'}, nullable: {col[3]}, "
                            f"samples: {_format_samples(sample_values)})"
                        )

        except Exception as e:
            schema_info.append(f"\nError getting schema for {table_name}: {str(e)}")

        return "\n".join(schema_info)

    def is_available(self) -> bool:
        """
        检查SQL Server数据源是否可用

        Returns:
            数据源是否可用的布尔值
        """
        try:
            engine = self._get_engine()

            with engine.connect() as conn:
                from sqlalchemy import text
                result = conn.execute(text("SELECT 1"))
                result.fetchone()

            return True

        except Exception as e:
            return False

    def get_table_row_count(self, table_name: str) -> int:
        """
        获取表的行数

        Args:
            table_name: 表名

        Returns:
            表的行数
        """
        engine = self._get_engine()

        try:
            from sqlalchemy import text

            with engine.connect() as conn:
                count = conn.execute(
                    text(f"SELECT COUNT(*) FROM {self.schema}.{table_name}")
                )
                return count.scalar()

        except Exception as e:
            raise Exception(f"Failed to get row count for table {table_name}: {str(e)}")

    def close(self):
        """关闭数据库连接"""
        if self._connection:
            self._connection.close()
            self._connection = None

        if self._engine:
            self._engine.dispose()
            self._engine = None

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
