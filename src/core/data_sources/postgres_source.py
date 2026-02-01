"""PostgreSQL数据源策略实现

该类实现了PostgreSQL数据源接口，支持：
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


class PostgreSQLDataSource(DataSourceStrategy):
    """PostgreSQL数据源策略实现"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "postgres",
        user: str = "postgres",
        password: str = "postgres",
        schema: str = "public",
        connection_params: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化PostgreSQL数据源
        """
        config = get_config()

        # Priority: explicit args > config > defaults
        self.host = (
            host if host != "localhost" else (config.data_source.pg_host or "localhost")
        )
        # Handle port conversion safely
        config_port = config.data_source.pg_port
        if isinstance(config_port, str) and config_port.isdigit():
            config_port = int(config_port)
        elif isinstance(config_port, str):
            # Fallback if env var resolution failed or is empty
            config_port = 5432

        self.port = port if port != 5432 else (config_port or 5432)
        self.database = (
            database
            if database != "postgres"
            else (config.data_source.pg_database or "postgres")
        )
        self.user = (
            user if user != "postgres" else (config.data_source.pg_user or "postgres")
        )
        self.password = (
            password
            if password != "postgres"
            else (config.data_source.pg_password or "postgres")
        )
        self.schema = schema
        self.connection_params = connection_params or {}

        self._engine = None
        self._connection = None

    def _get_connection_string(self) -> str:
        """构建PostgreSQL连接字符串"""
        base_url = f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        return base_url

    def _get_engine(self):
        """获取SQLAlchemy engine"""
        if self._engine is None:
            try:
                from sqlalchemy import create_engine

                connection_string = self._get_connection_string()

                # 添加额外的连接参数
                if self.connection_params:
                    connection_string += "?"
                    params = "&".join(
                        [f"{k}={v}" for k, v in self.connection_params.items()]
                    )
                    connection_string += params

                self._engine = create_engine(connection_string)

            except ImportError:
                raise ImportError(
                    "sqlalchemy is required for PostgreSQL data source. "
                    "Install it with: pip install sqlalchemy psycopg2-binary"
                )

        return self._engine

    def load_data(self, table_name: str, limit: Optional[int] = None) -> pd.DataFrame:
        """
        从PostgreSQL表加载数据到DataFrame

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
                if limit:
                    query = text(
                        f"SELECT * FROM {self.schema}.{table_name} LIMIT {limit}"
                    )
                else:
                    query = text(f"SELECT * FROM {self.schema}.{table_name}")

                result = conn.execute(query)
                # Get column names from cursor description
                columns = [desc[0] for desc in result.cursor.description]
                # Fetch all rows
                rows = result.fetchall()
                # Create DataFrame
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
            "source_type": "postgresql",
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "schema": self.schema,
            "user": self.user,
            "tables": [
                "cost_database",
                "rate_table",
                "cc_mapping",
                "cost_text_mapping",
            ],
        }

    def get_context(self) -> Dict[str, str]:
        """
        返回业务逻辑和上下文信息 (Generic Implementation)

        Returns:
            包含上下文信息的字典
        """
        engine = self._get_engine()

        context = {
            "data_source_type": "postgresql",
            "database": self.database,
            "schema": self.schema,
            "tables": {},
        }

        # 获取表信息
        try:
            from sqlalchemy import text

            with engine.connect() as conn:
                # 获取表名
                tables_query = text(
                    """
                    SELECT tablename 
                    FROM pg_tables 
                    WHERE schemaname = :schema
                    ORDER BY tablename
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
                # Get column names
                columns = [desc[0] for desc in result.cursor.description]
                # Fetch rows
                rows = result.fetchall()
                # Create DataFrame
                df = pd.DataFrame(rows, columns=columns)

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

        try:
            with engine.connect() as conn:
                for table_name in table_names:
                    # 获取表结构
                    columns_query = text(
                        """
                        SELECT 
                            column_name,
                            data_type,
                            character_maximum_length,
                            is_nullable
                        FROM information_schema.columns
                        WHERE table_name = :table_name
                            AND table_schema = :schema
                        ORDER BY ordinal_position
                    """
                    )

                    columns = conn.execute(
                        columns_query,
                        {"table_name": table_name.lower(), "schema": self.schema},
                    )

                    schema_info.append(f"\n=== Table: {table_name} ===\n")

                    for col in columns:
                        schema_info.append(
                            f"{col[0]:<30} {col[1]} "
                            f"(max length: {col[2] or 'N/A'}, nullable: {col[3]})"
                        )

        except Exception as e:
            schema_info.append(f"\nError getting schema for {table_name}: {str(e)}")

        return "\n".join(schema_info)

    def is_available(self) -> bool:
        """
        检查PostgreSQL数据源是否可用

        Returns:
            数据源是否可用的布尔值
        """
        try:
            engine = self._get_engine()

            with engine.connect() as conn:
                # 测试连接 - SQLAlchemy 2.0+ 需要不同的语法
                from sqlalchemy import text

                result = conn.execute(text("SELECT 1"))
                result.fetchone()

            return True

        except Exception as e:
            return False
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
