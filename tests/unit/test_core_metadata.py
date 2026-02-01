"""
Core Metadata 单元测试
测试核心元数据模块，验证表名解析、Schema 获取和业务规则提取功能。
"""

import pytest
from unittest.mock import MagicMock
from core.metadata import (
    resolve_table_names,
    get_table_schema,
    get_all_tables,
    get_table_relationships,
    get_sql_generation_rules
)

class TestCoreMetadata:
    """测试 core/metadata.py 模块"""

    @pytest.fixture
    def mock_skill(self):
        """创建一个 Mock Skill 对象"""
        skill = MagicMock()
        skill.get_metadata.return_value = {
            "keyword_table_map": {
                "cost": ["cost_table"],
                "rate": ["rate_table"]
            },
            "intent_table_map": {
                "allocation": ["alloc_table"]
            },
            "default_tables": ["default_table"],
            "table_schemas": {
                "cost_table": {"col1": "int"},
                "rate_table": {"col2": "float"}
            },
            "tables": {
                "Cost": "cost_table" # Alias
            },
            "relationships": {
                "cost_table": [{"target": "rate_table", "on": "key"}]
            }
        }
        skill.get_module_content.return_value = "Custom SQL Rules"
        return skill

    def test_resolve_table_names_keyword_match(self, mock_skill):
        """测试基于关键字的表名解析"""
        metadata = mock_skill.get_metadata()
        tables = resolve_table_names("Show me the cost", {}, metadata)
        assert "cost_table" in tables
        assert len(tables) == 1

    def test_resolve_table_names_intent_match(self, mock_skill):
        """测试基于意图的表名解析"""
        metadata = mock_skill.get_metadata()
        intent = {"intent_type": "allocation"}
        tables = resolve_table_names("Analyze allocation", intent, metadata)
        # Should match 'allocation' intent -> 'alloc_table'
        # And query "Analyze allocation" might not match keywords if not mapped
        assert "alloc_table" in tables

    def test_resolve_table_names_default(self, mock_skill):
        """测试默认表名回退"""
        metadata = mock_skill.get_metadata()
        tables = resolve_table_names("Hello world", {}, metadata)
        assert tables == ["default_table"]

    def test_resolve_table_names_no_metadata(self):
        """测试无元数据的情况"""
        tables = resolve_table_names("query", {}, None)
        assert tables == []

    def test_get_table_schema(self, mock_skill):
        """测试获取表结构"""
        metadata = mock_skill.get_metadata()
        schema = get_table_schema("cost_table", metadata)
        assert schema == {"col1": "int"}

    def test_get_table_schema_alias(self, mock_skill):
        """测试通过别名获取表结构"""
        metadata = mock_skill.get_metadata()
        schema = get_table_schema("Cost", metadata) # "Cost" maps to "cost_table"
        assert schema == {"col1": "int"}

    def test_get_all_tables(self, mock_skill):
        """测试获取所有表"""
        metadata = mock_skill.get_metadata()
        tables = get_all_tables(metadata)
        assert "cost_table" in tables
        assert "rate_table" in tables

    def test_get_table_relationships(self, mock_skill):
        """测试获取表关系"""
        metadata = mock_skill.get_metadata()
        rels = get_table_relationships(metadata)
        assert "cost_table" in rels
        assert rels["cost_table"][0]["target"] == "rate_table"

    def test_get_sql_generation_rules_default(self):
        """测试默认 SQL 生成规则"""
        rules = get_sql_generation_rules("postgresql", None)
        assert "PostgreSQL" in rules
        
        rules_sqlite = get_sql_generation_rules("excel", None)
        assert "SQLite" in rules_sqlite

    def test_get_sql_generation_rules_from_skill(self, mock_skill):
        """测试从 Skill 获取自定义 SQL 规则"""
        rules = get_sql_generation_rules("postgresql", mock_skill)
        assert rules == "Custom SQL Rules"
