"""配置管理模块"""

import os
import re
from pathlib import Path
from typing import Optional, Dict, Any, List

import yaml
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class ProviderConfig(BaseModel):
    """单个模型提供者配置"""

    provider: str = "openai"
    model_name: str = "gpt-4"
    api_key: str = ""
    base_url: Optional[str] = None
    temperature: float = 0.1
    max_tokens: int = 4096
    stream: bool = False
    description: Optional[str] = None
    model_kwargs: Dict[str, Any] = Field(default_factory=dict)  # 支持额外的模型参数


class ModelConfig(BaseModel):
    """模型配置"""

    active: str = "ollama"
    providers: Dict[str, ProviderConfig] = Field(default_factory=dict)

    # Legacy fields for backward compatibility (optional)
    provider: Optional[str] = None
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None

    def get_active_provider(self) -> ProviderConfig:
        """获取当前激活的提供商配置"""
        if self.active and self.active in self.providers:
            return self.providers[self.active]

        if self.providers:
            raise ValueError(
                f"Active model provider '{self.active}' not found in config.yaml."
            )

        # Fallback to legacy behavior if providers dict is empty but legacy fields exist
        if not self.providers and self.provider:
            return ProviderConfig(
                provider=self.provider,
                model_name=self.model_name or "gpt-4",
                api_key=self.api_key or "",
                base_url=self.base_url,
                temperature=self.temperature or 0.1,
                max_tokens=self.max_tokens or 4096,
            )

        raise ValueError("No model providers configured in config.yaml.")


class ServerConfig(BaseModel):
    """Server Config"""

    host: str = "0.0.0.0"
    port: int = 8000


class EmbeddingProviderConfig(BaseModel):
    """Embedding Provider Config"""

    model: str
    dims: int
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    description: Optional[str] = None


class EmbeddingConfig(BaseModel):
    """Embedding Config"""

    active: str = "ollama"
    providers: Dict[str, EmbeddingProviderConfig] = Field(default_factory=dict)


class KnowledgeBaseConfig(BaseModel):
    """Knowledge Base Config"""

    enabled: bool = True
    knowledge_dir: str = "knowledge"
    vector_db_path: str = ".vector_db"
    top_k: int = 3
    similarity_threshold: float = 0.3


class ExcelConfig(BaseModel):
    """Excel 配置"""

    max_preview_rows: int = 5
    default_result_limit: int = 20
    max_result_limit: int = 1000


class PostgreSQLConfig(BaseModel):
    """PostgreSQL 配置"""

    type: str = "postgresql"
    host: str = "localhost"
    port: int = 5432
    database: str = "postgres"
    user: str = "postgres"
    password: str = ""
    schema: str = "public"
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600
    connect_timeout: int = 10
    statement_timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 1


class SQLServerConfig(BaseModel):
    """SQL Server 配置"""

    type: str = "sqlserver"
    host: str = "localhost"
    port: int = 1433
    database: str = "master"
    user: str = "sa"
    password: str = ""
    driver: str = "ODBC Driver 17 for SQL Server"
    schema: str = "dbo"


class ExcelDataSourceConfig(BaseModel):
    """Excel 数据源配置"""

    type: str = "excel"
    file_paths: Dict[str, str] = Field(default_factory=dict)


class DataSourceConfig(BaseModel):
    """数据源配置"""

    type: str = "excel"  # 当前激活的数据源类型: excel, postgresql, sqlserver, auto
    config: Dict[str, Any] = Field(default_factory=dict)
    data_source_strategy: str = "auto"
    postgresql: PostgreSQLConfig = Field(default_factory=PostgreSQLConfig)
    sqlserver: SQLServerConfig = Field(default_factory=SQLServerConfig)
    excel: ExcelDataSourceConfig = Field(default_factory=ExcelDataSourceConfig)
    table_names: Dict[str, str] = Field(default_factory=dict)
    data_source_priority: Dict[str, int] = Field(default_factory=dict)


class LoggingConfig(BaseModel):
    """日志配置"""

    level: str = "INFO"
    format_max_lines: int = 15
    format_max_chars: int = 1000
    tool_input_truncate: int = 1000
    message_max_lines: int = 15
    message_max_chars: int = 1000


class AppConfig(BaseModel):
    """应用配置"""

    model: ModelConfig = Field(default_factory=ModelConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    knowledge_base: KnowledgeBaseConfig = Field(default_factory=KnowledgeBaseConfig)
    excel: ExcelConfig = Field(default_factory=ExcelConfig)
    data_source: DataSourceConfig = Field(default_factory=DataSourceConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


def _expand_env_vars(value: str) -> str:
    """展开环境变量 ${VAR} 或 ${VAR:default} 格式"""
    pattern = re.compile(r"\$\{(\w+)(?::([^}]*))?\}")

    def replacer(match):
        env_var = match.group(1)
        default_val = match.group(2) if match.group(2) is not None else ""
        return os.environ.get(env_var, default_val)

    return pattern.sub(replacer, value)


def _process_config_dict(config: dict) -> dict:
    """递归处理配置字典中的环境变量"""
    result = {}
    for key, value in config.items():
        if isinstance(value, str):
            result[key] = _expand_env_vars(value)
        elif isinstance(value, dict):
            result[key] = _process_config_dict(value)
        else:
            result[key] = value
    return result


def load_config(config_path: Optional[str] = None) -> AppConfig:
    """加载配置文件

    Args:
        config_path: 配置文件路径，默认为项目根目录的 config.yaml

    Returns:
        AppConfig 实例
    """
    if config_path is None:
        possible_paths = [
            Path("config.yaml"),
            Path("config/config.yaml"),
            Path(__file__).parent.parent.parent / "config.yaml",
            Path(__file__).parent.parent.parent / "config" / "config.yaml",
        ]
        for p in possible_paths:
            if p.exists():
                config_path = str(p)
                break

    if config_path and Path(config_path).exists():
        print(f"DEBUG: Loading config from {config_path}")
        with open(config_path, "r", encoding="utf-8") as f:
            raw_config = yaml.safe_load(f) or {}
        config_dict = _process_config_dict(raw_config)
        return AppConfig(**config_dict)

    return AppConfig()


_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """获取全局配置实例"""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def set_config(config: AppConfig) -> None:
    """设置全局配置实例"""
    global _config
    _config = config
