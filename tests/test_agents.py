"""Tests for workflow agents"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from langchain_core.messages import HumanMessage, AIMessage

from agents.load_context_agent import load_context_node
from agents.intent_analysis_agent import analyze_intent_node
from agents.sql_generation_agent import generate_sql_node
from agents.sql_validation_agent import validate_sql_node
from agents.execute_sql_agent import execute_sql_node
from agents.result_review_agent import review_result_node
from agents.refine_answer_agent import refine_answer_node
from skills.loader import Skill


class TestIntentAnalysisAgent:
    """Test intent analysis agent"""

    @pytest.fixture
    def mock_skill(self):
        """Create a mock skill"""
        skill = Mock(spec=Skill)
        skill.get_module.return_value = None
        return skill

    @pytest.fixture
    def sample_state(self, mock_skill):
        """Create a sample state"""
        return {
            "messages": [HumanMessage(content="test query")],
            "user_query": "test query",
            "intent_analysis": None,
            "skill": mock_skill,
            "skill_name": "test"
        }

    def test_analyze_intent_basic(self, sample_state):
        """Test basic intent analysis"""
        state = sample_state
        result = analyze_intent_node(state)
        
        assert "intent_analysis" in result
        assert result["intent_analysis"] is not None

    def test_analyze_intent_with_skill(self, sample_state, mock_skill):
        """Test intent analysis with skill context"""
        state = sample_state
        
        result = analyze_intent_node(state)
        
        assert "intent_analysis" in result


class TestLoadContextAgent:
    """Test load context agent"""

    @pytest.fixture
    def mock_skill(self):
        """Create a mock skill"""
        skill = Mock(spec=Skill)
        skill.get_metadata.return_value = {
            "tables": {
                "users": {
                    "columns": ["id", "name", "age"]
                }
            }
        }
        return skill

    @pytest.fixture
    def sample_state(self, mock_skill):
        """Create a sample state"""
        return {
            "user_query": "show users",
            "intent_analysis": {"intent": "query", "params": {}},
            "table_names": None,
            "skill": mock_skill,
            "skill_name": "test"
        }

    def test_load_context(self, sample_state):
        """Test loading context"""
        state = sample_state
        result = load_context_node(state)
        
        assert "table_names" in result
        assert result["table_names"] is not None

    def test_load_context_with_metadata(self, sample_state, mock_skill):
        """Test loading context with skill metadata"""
        state = sample_state
        mock_skill.get_metadata.return_value = {"tables": {"users": {}}}
        
        result = load_context_node(state)
        
        assert "table_names" in result


class TestSQLGenerationAgent:
    """Test SQL generation agent"""

    @pytest.fixture
    def mock_skill(self):
        """Create a mock skill"""
        skill = Mock(spec=Skill)
        skill.get_business_rules.return_value = []
        skill.get_sql_templates.return_value = {}
        skill.get_module_content.return_value = ""
        return skill

    @pytest.fixture
    def sample_state(self, mock_skill):
        """Create a sample state"""
        return {
            "user_query": "show all users",
            "intent_analysis": {"intent": "query", "params": {"table": "users"}},
            "table_names": ["users"],
            "sql_query": None,
            "retry_count": 0,
            "skill": mock_skill,
            "skill_name": "test"
        }

    @patch('agents.sql_generation_agent.get_llm')
    def test_generate_sql(self, mock_get_llm, sample_state):
        """Test SQL generation"""
        mock_llm = Mock()
        mock_llm.invoke.return_value.content = "SELECT * FROM users"
        mock_get_llm.return_value = mock_llm
        
        state = sample_state
        result = generate_sql_node(state)
        
        assert "sql_query" in result
        assert result["sql_query"] is not None

    @patch('agents.sql_generation_agent.get_llm')
    def test_generate_sql_with_business_rules(self, mock_get_llm, sample_state, mock_skill):
        """Test SQL generation with business rules"""
        mock_llm = Mock()
        mock_llm.invoke.return_value.content = "SELECT * FROM users WHERE age > 18"
        mock_get_llm.return_value = mock_llm
        
        mock_skill.get_business_rules.return_value = [
            {"name": "age_filter", "rule": "Always filter age > 18"}
        ]
        
        state = sample_state
        result = generate_sql_node(state)
        
        assert "sql_query" in result


class TestSQLValidationAgent:
    """Test SQL validation agent"""

    @pytest.fixture
    def mock_skill(self):
        """Create a mock skill"""
        skill = Mock(spec=Skill)
        skill.get_module_content.return_value = ""
        return skill

    @pytest.fixture
    def sample_state(self, mock_skill):
        """Create a sample state"""
        return {
            "user_query": "show users",
            "sql_query": "SELECT * FROM users",
            "sql_valid": False,
            "retry_count": 0,
            "skill": mock_skill,
            "skill_name": "test"
        }

    @patch('agents.sql_validation_agent.get_llm')
    def test_validate_sql_valid(self, mock_get_llm, sample_state):
        """Test validation of valid SQL"""
        mock_llm = Mock()
        mock_llm.invoke.return_value.content = '{"valid": true, "reasoning": "Valid SQL"}'
        mock_get_llm.return_value = mock_llm
        
        state = sample_state
        result = validate_sql_node(state)
        
        assert "sql_valid" in result
        assert result["sql_valid"] is True

    @patch('agents.sql_validation_agent.get_llm')
    def test_validate_sql_invalid(self, mock_get_llm, sample_state):
        """Test validation of invalid SQL"""
        mock_llm = Mock()
        mock_llm.invoke.return_value.content = '{"valid": false, "reasoning": "Invalid SQL"}'
        mock_get_llm.return_value = mock_llm
        
        state = sample_state
        result = validate_sql_node(state)
        
        assert "sql_valid" in result
        assert result["sql_valid"] is False


class TestExecuteSQLAgent:
    """Test SQL execution agent"""

    @pytest.fixture
    def mock_skill(self):
        """Create a mock skill"""
        skill = Mock(spec=Skill)
        return skill

    @pytest.fixture
    def sample_state(self, mock_skill):
        """Create a sample state"""
        return {
            "sql_query": "SELECT * FROM users",
            "execution_result": None,
            "error_message": None,
            "retry_count": 0,
            "data_source_type": "excel",
            "skill": mock_skill,
            "skill_name": "test"
        }

    @patch('agents.execute_sql_agent.get_data_manager')
    def test_execute_sql_success(self, mock_get_dm, sample_state):
        """Test successful SQL execution"""
        mock_manager = Mock()
        mock_manager.execute_query.return_value = {"data": [{"id": 1, "name": "test"}]}
        mock_get_dm.return_value = mock_manager
        
        state = sample_state
        result = execute_sql_node(state)
        
        assert "execution_result" in result
        assert result["execution_result"] is not None

    @patch('agents.execute_sql_agent.get_data_manager')
    def test_execute_sql_error(self, mock_get_dm, sample_state):
        """Test SQL execution with error"""
        mock_manager = Mock()
        mock_manager.execute_query.side_effect = Exception("SQL error")
        mock_get_dm.return_value = mock_manager
        
        state = sample_state
        result = execute_sql_node(state)
        
        assert "error_message" in result
        assert result["error_message"] is not None


class TestResultReviewAgent:
    """Test result review agent"""

    @pytest.fixture
    def mock_skill(self):
        """Create a mock skill"""
        skill = Mock(spec=Skill)
        skill.get_module_content.return_value = ""
        return skill

    @pytest.fixture
    def sample_state(self, mock_skill):
        """Create a sample state"""
        return {
            "user_query": "show users",
            "execution_result": "Result data",
            "review_passed": None,
            "review_message": None,
            "retry_count": 0,
            "skill": mock_skill,
            "skill_name": "test"
        }

    @patch('agents.result_review_agent.get_llm')
    def test_review_result_passed(self, mock_get_llm, sample_state):
        """Test result review passed"""
        mock_llm = Mock()
        mock_llm.invoke.return_value.content = '{"passed": true, "message": "Review passed", "confidence": 0.9}'
        mock_get_llm.return_value = mock_llm
        
        state = sample_state
        result = review_result_node(state)
        
        assert "review_passed" in result
        assert result["review_passed"] is True

    @patch('agents.result_review_agent.get_llm')
    def test_review_result_failed(self, mock_get_llm, sample_state):
        """Test result review failed"""
        mock_llm = Mock()
        mock_llm.invoke.return_value.content = '{"passed": false, "message": "Review failed", "confidence": 0.3}'
        mock_get_llm.return_value = mock_llm
        
        state = sample_state
        result = review_result_node(state)
        
        assert "review_passed" in result
        assert result["review_passed"] is False


class TestRefineAnswerAgent:
    """Test answer refinement agent"""

    @pytest.fixture
    def mock_skill(self):
        """Create a mock skill"""
        skill = Mock(spec=Skill)
        skill.get_module_content.return_value = ""
        return skill

    @pytest.fixture
    def sample_state(self, mock_skill):
        """Create a sample state"""
        return {
            "user_query": "show users",
            "execution_result": "Result data",
            "review_passed": True,
            "review_message": None,
            "messages": [HumanMessage(content="show users")],
            "skill": mock_skill,
            "skill_name": "test"
        }

    @patch('agents.refine_answer_agent.get_llm')
    def test_refine_answer(self, mock_get_llm, sample_state):
        """Test answer refinement"""
        mock_llm = Mock()
        mock_llm.invoke.return_value = AIMessage(content="Refined answer")
        mock_get_llm.return_value = mock_llm
        
        state = sample_state
        result = refine_answer_node(state)
        
        assert "review_message" in result
        assert result["review_message"] is not None

    @patch('agents.refine_answer_agent.get_llm')
    def test_refine_answer_with_execution_result(self, mock_get_llm, sample_state):
        """Test answer refinement with execution result"""
        mock_llm = Mock()
        mock_llm.invoke.return_value = AIMessage(content="Users: 1, 2, 3")
        mock_get_llm.return_value = mock_llm
        
        state = sample_state
        state["execution_result"] = "User data"
        
        result = refine_answer_node(state)
        
        assert "review_message" in result
        assert "Users" in result["review_message"]
