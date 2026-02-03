"""数据源配置管理器

从配置文件读取数据源配置并应用到数据源管理器
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

from src.config.settings import load_config, get_config
from src.core.interfaces import IDataSourceConfig


def load_data_source_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    加载数据源配置

    Args:
        config_path: 配置文件路径

    Returns:
        包含数据源配置的字典
    """
    if config_path is None:
        config_path = "config.yaml"

    config_file_path = Path(config_path)

    if not config_file_path.exists():
        raise FileNotFoundError(
            f"Data source config file not found: {config_file_path}"
        )

    with open(config_file_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    return config.get("data_source", {})


def apply_data_source_config(config_path: Optional[str] = None) -> None:
    """
    应用数据源配置到数据源管理器

    Args:
        config_path: 配置文件路径
    """
    from src.core.data_sources.manager import get_data_source_manager

    config = load_data_source_config(config_path)

    # 获取策略配置
    strategy_name = config.get("type", "auto")
    data_source_strategy = config.get("data_source_strategy", "auto")

    # 设置数据源策略
    manager = get_data_source_manager()

    if strategy_name == "postgresql":
        try:
            from src.core.data_sources.postgres_source import PostgreSQLDataSource

            # 读取PostgreSQL配置
            pg_config = config.get("postgresql", {})

            # 创建PostgreSQL数据源
            pg_source = PostgreSQLDataSource(
                host=pg_config.get("host", "localhost"),
                port=pg_config.get("port", 5432),
                database=pg_config.get("database", "cost_allocation"),
                user=pg_config.get("user", "postgres"),
                password=pg_config.get("password", ""),
                schema=pg_config.get("schema", "public"),
            )

            # 验证连接
            if not pg_source.is_available():
                raise ConnectionError(
                    "Cannot connect to PostgreSQL. Please check configuration."
                )

            # 更新管理器
            manager._available_strategies["postgresql"] = pg_source

            print("✅ PostgreSQL数据源配置成功")
            print(f"   Host: {pg_config.get('host', 'localhost')}")
            print(f"   Database: {pg_config.get('database', 'cost_allocation')}")
            print(f"   Schema: {pg_config.get('schema', 'public')}")

            # 设置当前策略
            manager.set_strategy(data_source_strategy)

        except ImportError as e:
            raise ImportError(
                f"Cannot import PostgreSQL dependencies. "
                "Install with: pip install sqlalchemy psycopg2-binary"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to configure PostgreSQL data source: {e}")

    elif strategy_name == "excel":
        try:
            from src.core.data_sources.excel_source import ExcelDataSource

            # 读取Excel配置
            excel_config = config.get("excel", {})

            print("✅ Excel数据源配置成功")
            # Excel数据源不需要连接验证

            # 设置当前策略
            manager.set_strategy(data_source_strategy)

        except Exception as e:
            raise RuntimeError(f"Failed to configure Excel data source: {e}")

    else:
        raise ValueError(f"Unknown data source type: {strategy_name}")


def get_postgresql_connection_string(config_path: Optional[str] = None) -> str:
    """
    获取PostgreSQL连接字符串

    Args:
        config_path: 配置文件路径

    Returns:
        PostgreSQL连接字符串
    """
    config = load_data_source_config(config_path)
    pg_config = config.get("postgresql", {})

    return f"postgresql://{pg_config.get('user', 'postgres')}:{pg_config.get('password', '')}@{pg_config.get('host', 'localhost')}:{pg_config.get('port', 5432)}/{pg_config.get('database', 'cost_allocation')}"


def validate_data_source_config(config_path: Optional[str] = None) -> bool:
    """
    验证数据源配置

    Args:
        config_path: 配置文件路径

    Returns:
        配置是否有效
    """
    try:
        config = load_data_source_config(config_path)

        # 检查必需的配置项
        if config.get("type") == "postgresql":
            pg_config = config.get("postgresql", {})

            required_fields = ["host", "port", "database", "user"]
            for field in required_fields:
                if not pg_config.get(field):
                    print(f"⚠️  Missing required field: {field}")
                    return False

            # 验证端口
            try:
                port = int(pg_config.get("port", 5432))
                if port < 1 or port > 65535:
                    print("⚠️  Invalid port number: {port}")
                    return False
            except ValueError:
                print(f"⚠️  Invalid port format: {pg_config.get('port', 5432)}")
                return False

        elif config.get("type") == "excel":
            excel_config = config.get("excel", {})

            # Excel配置是可选的
            pass

        else:
            print(f"⚠️  Unknown data source type: {config.get('type')}")
            return False

        return True

    except Exception as e:
        print(f"⚠️  Configuration validation failed: {e}")
        return False


def switch_data_source(strategy_name: str, config_path: Optional[str] = None) -> None:
    """
    切换数据源

    Args:
        strategy_name: 策略名称 (auto, postgresql, excel)
        config_path: 配置文件路径
    """
    try:
        apply_data_source_config(config_path)
        print(f"\n✅ 数据源已切换为: {strategy_name}")
    except Exception as e:
        print(f"\n❌ 切换数据源失败: {e}")


def get_current_data_source_info(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    获取当前数据源信息

    Args:
        config_path: 配置文件路径

    Returns:
        包含数据源信息的字典
    """
    from src.core.data_sources.manager import get_data_source_manager
    from src.core.data_sources.tools import get_data_source_info

    manager = get_data_source_manager()
    return get_data_source_info()


def test_data_source_connection(config_path: Optional[str] = None) -> bool:
    """
    测试数据源连接

    Args:
        config_path: 配置文件路径

    Returns:
        连接是否成功
    """
    try:
        config = load_data_source_config(config_path)

        if config.get("type") == "postgresql":
            print("测试PostgreSQL连接...")

            pg_config = config.get("postgresql", {})

            try:
                from src.core.data_sources.postgres_source import PostgreSQLDataSource

                pg_source = PostgreSQLDataSource(
                    host=pg_config.get("host", "localhost"),
                    port=pg_config.get("port", 5432),
                    database=pg_config.get("database", "cost_allocation"),
                    user=pg_config.get("user", "postgres"),
                    password=pg_config.get("password", ""),
                    schema=pg_config.get("schema", "public"),
                )

                available = pg_source.is_available()

                if available:
                    print("✅ PostgreSQL连接测试成功")
                else:
                    print("❌ PostgreSQL连接测试失败")

                return available

            except Exception as e:
                print(f"❌ 测试连接时出错: {e}")
                return False

        elif config.get("type") == "excel":
            print("✅ Excel数据源配置完成（无需测试连接）")
            return True

        else:
            print(f"❌ 未知的数据源类型: {config.get('type')}")
            return False

    except Exception as e:
        print(f"❌ 测试数据源连接时出错: {e}")
        return False


if __name__ == "__main__":
    # 测试代码
    print("Testing data source configuration manager")

    # 验证配置文件
    config_path = "config_postgres.yaml"
    if Path(config_path).exists():
        print(f"\n✅ 找到配置文件: {config_path}")

        is_valid = validate_data_source_config(config_path)
        print(f"配置有效性: {'有效' if is_valid else '无效'}")

        if is_valid:
            # 测试连接
            is_connected = test_data_source_connection(config_path)
            print(f"连接状态: {'成功' if is_connected else '失败'}")

            # 获取数据源信息
            info = get_current_data_source_info(config_path)
            print(f"\n当前数据源信息:")
            print(f"  类型: {info.get('current_strategy')}")
            print(f"  可用: {info.get('is_available')}")
            print(f"  策略: {', '.join(info.get('available_strategies', []))}")
    else:
        print("配置验证失败，请检查配置文件")
