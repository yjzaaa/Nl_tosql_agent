"""Basic smoke tests to verify test setup"""

import pytest


def test_python_version():
    """Test that Python version is compatible"""
    import sys
    assert sys.version_info >= (3, 10), "Python 3.10+ required"


def test_imports():
    """Test that basic imports work"""
    from skills.loader import SkillLoader, Skill
    from nl_to_sql_agent import NLToSQLAgent
    from workflow.skill_aware import SkillAwareWorkflow
    from config.settings import AppConfig, load_config
    
    assert SkillLoader is not None
    assert Skill is not None
    assert NLToSQLAgent is not None
    assert SkillAwareWorkflow is not None
    assert AppConfig is not None
    assert load_config is not None


def test_project_structure():
    """Test that project structure is correct"""
    from pathlib import Path
    
    project_root = Path(__file__).parent.parent
    src_dir = project_root / "src"
    tests_dir = project_root / "tests"
    
    assert src_dir.exists(), "src directory should exist"
    assert tests_dir.exists(), "tests directory should exist"
    
    required_files = [
        "src/main.py",
        "src/nl_to_sql_agent.py",
        "src/workflow/skill_aware.py",
        "src/skills/loader.py",
        "src/config/settings.py",
    ]
    
    for file_path in required_files:
        full_path = project_root / file_path
        assert full_path.exists(), f"{file_path} should exist"


def test_config_loading():
    """Test that config loading works"""
    from config.settings import load_config, AppConfig
    
    config = load_config()
    
    assert isinstance(config, AppConfig)
    assert hasattr(config, 'model')
    assert hasattr(config, 'excel')
    assert hasattr(config, 'data_source')
    assert hasattr(config, 'logging')


def test_skill_loader_structure():
    """Test that SkillLoader has expected structure"""
    from skills.loader import SkillLoader, Skill, SkillModule, MultiSkillLoader
    
    assert hasattr(SkillLoader, 'load_skill')
    assert hasattr(SkillLoader, 'list_available_skills')
    assert hasattr(Skill, 'add_module')
    assert hasattr(Skill, 'get_module')
    assert hasattr(MultiSkillLoader, 'load_skill')


def test_workflow_structure():
    """Test that workflow has expected structure"""
    from workflow.skill_aware import SkillAwareWorkflow, SkillAwareState
    from typing import get_origin
    
    assert hasattr(SkillAwareWorkflow, 'build_graph')
    assert hasattr(SkillAwareWorkflow, 'get_graph')
    # TypedDict is a special type, check if it has __annotations__
    assert hasattr(SkillAwareState, '__annotations__')


def test_agent_structure():
    """Test that NLToSQLAgent has expected structure"""
    from nl_to_sql_agent import NLToSQLAgent
    
    assert hasattr(NLToSQLAgent, '__init__')
    assert hasattr(NLToSQLAgent, 'query')
    assert hasattr(NLToSQLAgent, 'reload_skill')
    assert hasattr(NLToSQLAgent, 'list_available_skills')
