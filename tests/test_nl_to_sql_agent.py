"""Tests for NLToSQLAgent class"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from nl_to_sql_agent import NLToSQLAgent
from skills.loader import Skill, SkillLoader


class TestNLToSQLAgent:
    """Test NLToSQLAgent class"""

    @pytest.fixture
    def mock_skill(self, temp_skill_dir):
        """Create a mock skill for testing"""
        skill_md = temp_skill_dir / "SKILL.md"
        skill_md.write_text("""---
name: test-skill
version: "1.0.0"
description: "Test skill"
---
""")
        return Skill(name="test-skill", skill_path=temp_skill_dir)

    @pytest.fixture
    def mock_skill_loader(self, temp_skill_dir, mock_skill):
        """Create a mock skill loader"""
        loader = Mock(spec=SkillLoader)
        loader.load_skill.return_value = mock_skill
        return loader

    def test_agent_init_with_skill_path(self, temp_skill_dir):
        """Test agent initialization with skill path"""
        agent = NLToSQLAgent(skill_path=str(temp_skill_dir), skill_name="test-skill")
        
        assert agent.skill_path == Path(temp_skill_dir)
        assert agent.skill_name == "test-skill"

    def test_agent_init_defaults(self):
        """Test agent initialization with defaults"""
        agent = NLToSQLAgent()
        
        assert agent.skill_path == Path.cwd() / "skills"
        assert agent.skill_name == "nl-to-sql-agent"

    @patch('nl_to_sql_agent.SkillLoader')
    def test_initialize_loads_skill(self, mock_loader_class, temp_skill_dir):
        """Test that initialization loads skill"""
        mock_skill = Mock(spec=Skill)
        mock_skill.name = "test"
        mock_skill.version = "1.0.0"
        
        mock_loader = Mock(spec=SkillLoader)
        mock_loader.load_skill.return_value = mock_skill
        mock_loader_class.return_value = mock_loader
        
        agent = NLToSQLAgent(skill_path=str(temp_skill_dir), skill_name="test")
        
        mock_loader.load_skill.assert_called_once_with("test")
        assert agent.skill == mock_skill

    @patch('nl_to_sql_agent.SkillLoader')
    def test_initialize_without_skill(self, mock_loader_class, temp_skill_dir):
        """Test initialization when skill is not found"""
        mock_loader = Mock(spec=SkillLoader)
        mock_loader.load_skill.return_value = None
        mock_loader_class.return_value = mock_loader
        
        agent = NLToSQLAgent(skill_path=str(temp_skill_dir), skill_name="nonexistent")
        
        assert agent.skill is None
        assert agent.workflow is not None

    def test_query_basic(self, temp_skill_dir):
        """Test basic query execution"""
        skill_md = temp_skill_dir / "SKILL.md"
        skill_md.write_text("---\nname: test\nversion: 1.0.0\n---")
        
        agent = NLToSQLAgent(skill_path=str(temp_skill_dir), skill_name="test")
        
        result = agent.query("test query")
        
        assert "query" in result
        assert result["query"] == "test query"

    def test_query_with_kwargs(self, temp_skill_dir):
        """Test query execution with additional kwargs"""
        skill_md = temp_skill_dir / "SKILL.md"
        skill_md.write_text("---\nname: test\nversion: 1.0.0\n---")
        
        agent = NLToSQLAgent(skill_path=str(temp_skill_dir), skill_name="test")
        
        result = agent.query("test query", trace_id="test-123", data_source_type="excel")
        
        assert result["query"] == "test query"

    @patch('nl_to_sql_agent.SkillLoader')
    def test_query_workflow_exception(self, mock_loader_class, temp_skill_dir):
        """Test query when workflow raises exception"""
        mock_loader = Mock(spec=SkillLoader)
        mock_loader.load_skill.return_value = None
        mock_loader_class.return_value = mock_loader
        
        agent = NLToSQLAgent(skill_path=str(temp_skill_dir), skill_name="test")
        
        with patch.object(agent.workflow, 'get_graph', side_effect=Exception("Workflow error")):
            result = agent.query("test query")
            
            assert result["success"] is False
            assert "error" in result

    @patch('nl_to_sql_agent.SkillLoader')
    def test_reload_skill(self, mock_loader_class, temp_skill_dir):
        """Test reloading skill"""
        mock_skill1 = Mock(spec=Skill)
        mock_skill1.name = "test"
        mock_skill1.version = "1.0.0"
        
        mock_skill2 = Mock(spec=Skill)
        mock_skill2.name = "test"
        mock_skill2.version = "2.0.0"
        
        mock_loader = Mock(spec=SkillLoader)
        mock_loader.load_skill.side_effect = [mock_skill1, mock_skill2]
        mock_loader_class.return_value = mock_loader
        
        agent = NLToSQLAgent(skill_path=str(temp_skill_dir), skill_name="test")
        agent.reload_skill("test")
        
        assert agent.skill == mock_skill2

    @patch('nl_to_sql_agent.SkillLoader')
    def test_reload_skill_new_name(self, mock_loader_class, temp_skill_dir):
        """Test reloading with new skill name"""
        mock_skill1 = Mock(spec=Skill)
        mock_skill1.name = "skill1"
        
        mock_skill2 = Mock(spec=Skill)
        mock_skill2.name = "skill2"
        
        mock_loader = Mock(spec=SkillLoader)
        mock_loader.load_skill.side_effect = [mock_skill1, mock_skill2]
        mock_loader_class.return_value = mock_loader
        
        agent = NLToSQLAgent(skill_path=str(temp_skill_dir), skill_name="skill1")
        agent.reload_skill("skill2")
        
        assert agent.skill_name == "skill2"
        assert agent.skill == mock_skill2

    @patch('nl_to_sql_agent.SkillLoader')
    def test_list_available_skills(self, mock_loader_class, temp_skill_dir):
        """Test listing available skills"""
        mock_loader = Mock(spec=SkillLoader)
        mock_loader.list_available_skills.return_value = ["skill1", "skill2", "skill3"]
        mock_loader.load_skill.return_value = None
        mock_loader_class.return_value = mock_loader
        
        agent = NLToSQLAgent(skill_path=str(temp_skill_dir), skill_name="test")
        skills = agent.list_available_skills()
        
        assert skills == ["skill1", "skill2", "skill3"]

    @patch('nl_to_sql_agent.SkillLoader')
    def test_query_state_initialization(self, mock_loader_class, temp_skill_dir):
        """Test that query initializes state correctly"""
        mock_loader = Mock(spec=SkillLoader)
        mock_loader.load_skill.return_value = None
        mock_loader_class.return_value = mock_loader
        
        agent = NLToSQLAgent(skill_path=str(temp_skill_dir), skill_name="test")
        
        with patch.object(agent.workflow, 'get_graph') as mock_graph:
            mock_graph.return_value.invoke.return_value = {
                "sql_valid": True,
                "sql_query": "SELECT * FROM table",
                "execution_result": "test result",
                "review_message": "answer",
                "review_passed": True
            }
            
            result = agent.query("test query", trace_id="trace-123")
            
            assert result["trace_id"] == "trace-123"

    def test_query_result_structure(self, temp_skill_dir):
        """Test query result structure"""
        skill_md = temp_skill_dir / "SKILL.md"
        skill_md.write_text("---\nname: test\nversion: 1.0.0\n---")
        
        agent = NLToSQLAgent(skill_path=str(temp_skill_dir), skill_name="test")
        
        result = agent.query("test query")
        
        assert isinstance(result, dict)
        assert "success" in result
        assert "query" in result
        assert "sql" in result
        assert "result" in result
        assert "answer" in result
        assert "error" in result
        assert "skill" in result
