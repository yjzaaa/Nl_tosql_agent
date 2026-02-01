"""Tests for SkillLoader and Skill classes"""

import pytest
from pathlib import Path
import json
import yaml

from skills.loader import SkillLoader, Skill, SkillModule, MultiSkillLoader


class TestSkillModule:
    """Test SkillModule class"""

    def test_skill_module_creation(self, temp_skill_dir):
        """Test creating a skill module"""
        module_path = temp_skill_dir / "test_module.md"
        module_path.write_text("Test content")
        
        module = SkillModule(name="test_module", path=module_path)
        
        assert module.name == "test_module"
        assert module.path == module_path
        assert module.metadata == {}

    def test_load_content(self, temp_skill_dir):
        """Test loading module content"""
        module_path = temp_skill_dir / "test.md"
        expected_content = "Test content"
        module_path.write_text(expected_content)
        
        module = SkillModule(name="test", path=module_path)
        content = module.load_content()
        
        assert content == expected_content

    def test_load_content_from_string(self):
        """Test loading content from string"""
        expected_content = "Inline content"
        # Fix: Provide a dummy path as it is required
        module = SkillModule(name="test", path=Path("dummy"), content=expected_content)
        
        content = module.load_content()
        
        assert content == expected_content

    def test_to_dict(self, temp_skill_dir):
        """Test converting module to dict"""
        module_path = temp_skill_dir / "test.md"
        module_path.write_text("Test")
        
        module = SkillModule(name="test", path=module_path, metadata={"key": "value"})
        result = module.to_dict()
        
        assert result["name"] == "test"
        assert result["content"] == "Test"
        assert result["metadata"] == {"key": "value"}


class TestSkill:
    """Test Skill class"""

    def test_skill_creation(self, temp_skill_dir, sample_skill_content):
        """Test creating a skill"""
        skill_md = temp_skill_dir / "SKILL.md"
        skill_md.write_text(sample_skill_content)
        
        # Fix: Provide description manually as Skill constructor doesn't parse file
        skill = Skill(
            name="test-skill", 
            skill_path=temp_skill_dir,
            description="Test skill for unit testing",
            version="1.0.0",
            license="MIT"
        )
        
        assert skill.name == "test-skill"
        assert skill.version == "1.0.0"
        assert skill.description == "Test skill for unit testing"
        assert skill.license == "MIT"

    def test_add_module(self, temp_skill_dir):
        """Test adding a module to skill"""
        skill = Skill(name="test", skill_path=temp_skill_dir)
        module = SkillModule(name="module1", path=temp_skill_dir / "module1.md")
        
        skill.add_module(module)
        
        assert "module1" in skill.modules
        assert skill.modules["module1"] == module

    def test_get_module(self, temp_skill_dir):
        """Test getting a module from skill"""
        skill = Skill(name="test", skill_path=temp_skill_dir)
        module = SkillModule(name="module1", path=temp_skill_dir / "module1.md")
        skill.add_module(module)
        
        retrieved = skill.get_module("module1")
        
        assert retrieved == module
        assert skill.get_module("nonexistent") is None

    def test_get_module_content(self, temp_skill_dir):
        """Test getting module content"""
        skill = Skill(name="test", skill_path=temp_skill_dir)
        module_path = temp_skill_dir / "test.md"
        module_path.write_text("Test content")
        module = SkillModule(name="test", path=module_path)
        skill.add_module(module)
        
        content = skill.get_module_content("test")
        
        assert content == "Test content"

    def test_get_business_rules(self, temp_skill_dir, sample_business_rules):
        """Test getting business rules"""
        # Create module file manually
        rules_path = temp_skill_dir / "business_rules.md"
        rules_path.write_text(sample_business_rules)
        
        skill = Skill(name="test", skill_path=temp_skill_dir)
        # Add module to skill
        skill.add_module(SkillModule(name="business_rules", path=rules_path))
        
        rules = skill.get_business_rules()
        
        assert len(rules) == 2
        assert rules[0]["name"] == "field_naming"
        assert rules[1]["name"] == "amount_conversion"

    def test_get_metadata(self, temp_skill_dir, sample_metadata):
        """Test getting metadata"""
        refs_dir = temp_skill_dir / "references"
        refs_dir.mkdir()
        metadata_file = refs_dir / "metadata.md"
        metadata_file.write_text(sample_metadata)
        
        skill = Skill(name="test", skill_path=temp_skill_dir)
        skill.add_module(SkillModule(name="metadata", path=metadata_file))
        
        metadata = skill.get_metadata()
        
        assert "tables" in metadata
        assert "users" in metadata["tables"]

    def test_get_sql_templates(self, temp_skill_dir):
        """Test getting SQL templates"""
        templates_path = temp_skill_dir / "sql_templates.json"
        templates = {"select_all": "SELECT * FROM {table}"}
        templates_path.write_text(json.dumps(templates))
        
        skill = Skill(name="test", skill_path=temp_skill_dir)
        skill.add_module(SkillModule(name="sql_templates", path=templates_path))
        
        result = skill.get_sql_templates()
        
        assert result["select_all"] == "SELECT * FROM {table}"

    def test_list_scripts(self, temp_skill_dir):
        """Test listing scripts"""
        scripts_dir = temp_skill_dir / "scripts"
        scripts_dir.mkdir()
        
        (scripts_dir / "script1.py").write_text("# script 1")
        (scripts_dir / "script2.py").write_text("# script 2")
        (scripts_dir / "not_a_script.txt").write_text("text file")
        
        skill = Skill(name="test", skill_path=temp_skill_dir)
        scripts = skill.list_scripts()
        
        assert len(scripts) == 2
        script_names = [s["name"] for s in scripts]
        assert "script1" in script_names
        assert "script2" in script_names

    def test_execute_script(self, temp_skill_dir):
        """Test executing a script"""
        scripts_dir = temp_skill_dir / "scripts"
        scripts_dir.mkdir()
        
        script_path = scripts_dir / "test_script.py"
        script_path.write_text("print('Hello from script')")
        
        skill = Skill(name="test", skill_path=temp_skill_dir)
        result = skill.execute_script("test_script")
        
        assert result["success"] is True
        assert "Hello from script" in result["output"]

    def test_execute_nonexistent_script(self, temp_skill_dir):
        """Test executing a nonexistent script"""
        skill = Skill(name="test", skill_path=temp_skill_dir)
        result = skill.execute_script("nonexistent")
        
        assert result["success"] is False
        assert "not found" in result["error"]


class TestSkillLoader:
    """Test SkillLoader class"""

    def test_skill_loader_init(self, skills_dir):
        """Test SkillLoader initialization"""
        loader = SkillLoader(skills_dir)
        
        assert loader.skill_path == Path(skills_dir)
        assert loader._loaded_skills == {}

    def test_load_nonexistent_skill(self, temp_skill_dir):
        """Test loading a nonexistent skill"""
        # Use parent dir as loader root
        loader = SkillLoader(str(temp_skill_dir.parent))
        skill = loader.load_skill("nonexistent")
        
        assert skill is None

    def test_load_skill(self, temp_skill_dir, sample_skill_content):
        """Test loading a skill from directory"""
        skill_md = temp_skill_dir / "SKILL.md"
        skill_md.write_text(sample_skill_content)
        
        # Use parent dir as loader root
        loader = SkillLoader(str(temp_skill_dir.parent))
        skill = loader.load_skill("test_skill")
        
        assert skill is not None
        assert skill.name == "test-skill" # Name comes from metadata in SKILL.md

    def test_load_skill_cached(self, temp_skill_dir, sample_skill_content):
        """Test that skills are cached"""
        skill_md = temp_skill_dir / "SKILL.md"
        skill_md.write_text(sample_skill_content)
        
        loader = SkillLoader(str(temp_skill_dir.parent))
        skill1 = loader.load_skill("test_skill")
        skill2 = loader.load_skill("test_skill")
        
        assert skill1 is skill2

    def test_list_available_skills(self, temp_skill_dir, sample_skill_content):
        """Test listing available skills"""
        skill_md = temp_skill_dir / "SKILL.md"
        skill_md.write_text(sample_skill_content)
        
        another_skill_dir = temp_skill_dir.parent / "another_skill"
        another_skill_dir.mkdir(exist_ok=True)
        another_skill_md = another_skill_dir / "SKILL.md"
        another_skill_md.write_text(sample_skill_content)
        
        loader = SkillLoader(str(temp_skill_dir.parent))
        skills = loader.list_available_skills()
        
        assert len(skills) >= 2
        assert "test_skill" in skills
        assert "another_skill" in skills

    def test_reload_skill(self, temp_skill_dir, sample_skill_content):
        """Test reloading a skill"""
        skill_md = temp_skill_dir / "SKILL.md"
        skill_md.write_text(sample_skill_content)
        
        loader = SkillLoader(str(temp_skill_dir.parent))
        skill1 = loader.load_skill("test_skill")
        
        skill_md.write_text(sample_skill_content.replace("1.0.0", "2.0.0"))
        
        skill2 = loader.reload_skill("test_skill")
        
        assert skill2 is not None
        assert skill2.version == "2.0.0"

    def test_load_skill_with_modules(self, temp_skill_dir, sample_skill_content):
        """Test loading skill with modules"""
        skill_md = temp_skill_dir / "SKILL.md"
        skill_md.write_text(sample_skill_content)
        
        (temp_skill_dir / "module1.md").write_text("Module 1")
        (temp_skill_dir / "module2.md").write_text("Module 2")
        
        loader = SkillLoader(str(temp_skill_dir.parent))
        skill = loader.load_skill("test_skill")
        
        assert "module1" in skill.modules
        assert "module2" in skill.modules

    def test_load_skill_with_references(self, temp_skill_dir, sample_skill_content):
        """Test loading skill with references"""
        skill_md = temp_skill_dir / "SKILL.md"
        skill_md.write_text(sample_skill_content)
        
        refs_dir = temp_skill_dir / "references"
        refs_dir.mkdir()
        (refs_dir / "metadata.md").write_text("Metadata")
        
        loader = SkillLoader(str(temp_skill_dir.parent))
        skill = loader.load_skill("test_skill")
        
        assert "metadata" in skill.modules


class TestMultiSkillLoader:
    """Test MultiSkillLoader class"""

    def test_multi_skill_loader_init(self, temp_skill_dir):
        """Test MultiSkillLoader initialization"""
        another_dir = temp_skill_dir.parent / "skills2"
        another_dir.mkdir(exist_ok=True)
        
        loader = MultiSkillLoader([str(temp_skill_dir), str(another_dir)])
        
        assert len(loader.loaders) == 2

    def test_add_path(self, temp_skill_dir):
        """Test adding a path to MultiSkillLoader"""
        loader = MultiSkillLoader()
        loader.add_path(str(temp_skill_dir))
        
        assert len(loader.loaders) == 1
        assert loader.loaders[0].skill_path == Path(temp_skill_dir)

    def test_load_skill(self, temp_skill_dir, sample_skill_content):
        """Test loading skill from multiple paths"""
        skill_md = temp_skill_dir / "SKILL.md"
        skill_md.write_text(sample_skill_content)
        
        # Use parent dir to find test_skill
        loader = MultiSkillLoader([str(temp_skill_dir.parent)])
        skill = loader.load_skill("test_skill")
        
        assert skill is not None

    def test_list_all_skills(self, temp_skill_dir, sample_skill_content):
        """Test listing all skills from all paths"""
        skill_md = temp_skill_dir / "SKILL.md"
        skill_md.write_text(sample_skill_content)
        
        another_dir = temp_skill_dir.parent / "skills2"
        another_dir.mkdir(exist_ok=True)
        skill_md2 = another_dir / "SKILL.md"
        skill_md2.write_text(sample_skill_content)
        
        loader = MultiSkillLoader([str(temp_skill_dir.parent), str(another_dir.parent)])
        skills = loader.list_all_skills()
        
        assert "test_skill" in skills
        # Might be duplicated or handled by set, but we expect at least test_skill

    def test_reload_all(self, temp_skill_dir, sample_skill_content):
        """Test reloading all skills"""
        skill_md = temp_skill_dir / "SKILL.md"
        skill_md.write_text(sample_skill_content)
        
        loader = MultiSkillLoader([str(temp_skill_dir.parent)])
        loader.load_skill("test_skill")
        
        loader.reload_all()
        
        assert len(loader._skill_cache) == 0

    def test_get_skill_info(self, temp_skill_dir, sample_skill_content):
        """Test getting skill info"""
        skill_md = temp_skill_dir / "SKILL.md"
        skill_md.write_text(sample_skill_content)
        
        loader = MultiSkillLoader([str(temp_skill_dir.parent)])
        info = loader.get_skill_info("test_skill")
        
        assert info is not None
        assert info["name"] == "test-skill"
        assert info["version"] == "1.0.0"
        assert "modules" in info
