from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import yaml


@dataclass
class DataSourceConfig:
    type: str
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DataSourceConfig":
        return cls(
            type=data.get("type", "unknown"),
            enabled=data.get("enabled", True),
            config=data.get("config", {})
        )


@dataclass
class LLMConfig:
    provider: str = "openai"
    model: str = "qwen2.5-1.5b-instruct"
    temperature: float = 0.1
    max_tokens: int = 4096
    base_url: Optional[str] = None
    api_key: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LLMConfig":
        return cls(
            provider=data.get("provider", "openai"),
            model=data.get("model", "qwen2.5-1.5b-instruct"),
            temperature=data.get("temperature", 0.1),
            max_tokens=data.get("max_tokens", 4096),
            base_url=data.get("base_url"),
            api_key=data.get("api_key")
        )


@dataclass
class EmbeddingConfig:
    enabled: bool = True
    provider: str = "self_hosted"
    model: str = "qwen3-embedding-0.6b"
    dims: int = 1536
    api_url: Optional[str] = None
    api_key: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmbeddingConfig":
        return cls(
            enabled=data.get("enabled", True),
            provider=data.get("provider", "self_hosted"),
            model=data.get("model", "qwen3-embedding-0.6b"),
            dims=data.get("dims", 1536),
            api_url=data.get("api_url"),
            api_key=data.get("api_key")
        )


@dataclass
class SkillConfig:
    name: str = "nl-to-sql-agent"
    version: str = "1.0.0"
    data_sources: List[DataSourceConfig] = field(default_factory=list)
    llm: Optional[LLMConfig] = None
    embedding: Optional[EmbeddingConfig] = None
    raw_config: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "SkillConfig":
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillConfig":
        config = cls(
            name=data.get("skill", {}).get("name", "nl-to-sql-agent"),
            version=data.get("skill", {}).get("version", "1.0.0"),
            raw_config=data
        )

        if "data_sources" in data:
            for ds in data["data_sources"]:
                config.data_sources.append(DataSourceConfig.from_dict(ds))

        if "llm" in data:
            config.llm = LLMConfig.from_dict(data["llm"])

        if "embedding" in data:
            config.embedding = EmbeddingConfig.from_dict(data["embedding"])

        return config

    def get_data_source(self, ds_type: str) -> Optional[DataSourceConfig]:
        for ds in self.data_sources:
            if ds.type == ds_type:
                return ds
        return None

    def is_data_source_enabled(self, ds_type: str) -> bool:
        ds = self.get_data_source(ds_type)
        return ds.enabled if ds else False
