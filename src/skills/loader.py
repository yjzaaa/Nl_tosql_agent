import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class SkillModule:
    name: str
    path: Path
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def load_content(self) -> str:
        if self.path.exists():
            return self.path.read_text(encoding="utf-8")
        return self.content

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": str(self.path),
            "content": self.load_content(),
            "metadata": self.metadata
        }


@dataclass
class Skill:
    name: str
    version: str = "1.0.0"
    description: str = ""
    license: str = "MIT"
    skill_path: Optional[Path] = None
    modules: Dict[str, SkillModule] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)
    scripts: List[Dict[str, str]] = field(default_factory=list)

    def __post_init__(self):
        if self.skill_path is None:
            self.skill_path = Path.cwd() / "skills"

    def add_module(self, module: SkillModule):
        self.modules[module.name] = module

    def get_module(self, name: str) -> Optional[SkillModule]:
        return self.modules.get(name)

    def get_module_content(self, name: str) -> str:
        module = self.get_module(name)
        if module:
            return module.load_content()
        return ""

    def get_business_rules(self) -> List[Dict[str, Any]]:
        module = self.get_module("business_rules")
        if module:
            try:
                content = module.load_content()
                if content.strip().startswith("---"):
                    import yaml
                    # Parse Frontmatter
                    end_idx = content.find("---", 3)
                    if end_idx != -1:
                        yaml_content = content[3:end_idx].strip()
                        data = yaml.safe_load(yaml_content) or {}
                        return data.get("rules", [])
                    else:
                        # Fallback for pure YAML without closing ---
                        data = yaml.safe_load(content) or {}
                        return data.get("rules", [])
            except Exception as e:
                logger.warning(f"Failed to parse business rules: {e}")
        return []

    def get_sql_templates(self) -> Dict[str, Any]:
        module = self.get_module("sql_templates")
        if module:
            try:
                content = module.load_content()
                return json.loads(content)
            except json.JSONDecodeError:
                pass
        return {}

    def get_metadata(self) -> Dict[str, Any]:
        module = self.get_module("metadata")
        if module:
            try:
                content = module.load_content()
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0]
                    return json.loads(json_str)
            except Exception as e:
                logger.warning(f"Failed to parse metadata: {e}")
        return {}

    def list_scripts(self) -> List[Dict[str, str]]:
        """List available scripts in the skill"""
        if self.skill_path is None:
            return []

        scripts_path = self.skill_path / "scripts"
        if not scripts_path.exists():
            return []

        scripts = []
        for file in scripts_path.iterdir():
            if file.is_file() and file.suffix == ".py":
                scripts.append({
                    "name": file.stem,
                    "path": str(file),
                    "executable": True
                })
        return scripts

    def execute_script(
        self,
        script_name: str,
        args: Optional[list] = None,
        kwargs: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a script from this skill"""
        import subprocess
        import sys

        if self.skill_path is None:
            return {"success": False, "error": "No skill path set"}

        script_path = self.skill_path / "scripts" / f"{script_name}.py"

        if not script_path.exists():
            return {"success": False, "error": f"Script not found: {script_name}"}

        try:
            cmd = [sys.executable, str(script_path)]
            if args:
                cmd.extend(args)

            env = {"SKILL_PATH": str(self.skill_path)}

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                env={**__import__("os").environ, **env}
            )

            return {
                "success": result.returncode == 0,
                "return_code": result.returncode,
                "output": result.stdout,
                "error": result.stderr if result.stderr else None,
                "script": script_name
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Script timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}


class SkillLoader:
    def __init__(self, skill_path: Optional[str] = None):
        self.skill_path = Path(skill_path) if skill_path else Path.cwd() / "skills"
        self._loaded_skills: Dict[str, Skill] = {}

    def load_skill(self, skill_name: str) -> Optional[Skill]:
        if skill_name in self._loaded_skills:
            return self._loaded_skills[skill_name]

        skill_dir = self.skill_path / skill_name
        if not skill_dir.exists():
            logger.error(f"Skill not found: {skill_name}")
            return None

        skill = self._parse_skill_directory(skill_dir)
        if skill:
            self._loaded_skills[skill_name] = skill

        return skill

    def _parse_skill_directory(self, skill_dir: Path) -> Optional[Skill]:
        try:
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                logger.error(f"SKILL.md not found in {skill_dir}")
                return None

            content = skill_md.read_text(encoding="utf-8")
            metadata = self._parse_skill_metadata(content)

            skill = Skill(
                name=metadata.get("name", skill_dir.name),
                version=metadata.get("version", "1.0.0"),
                description=metadata.get("description", ""),
                license=metadata.get("license", "MIT"),
                skill_path=skill_dir
            )

            skill.config = self._load_skill_config(skill_dir)

            for module_file in skill_dir.glob("*.md"):
                if module_file.name != "SKILL.md":
                    module = SkillModule(
                        name=module_file.stem,
                        path=module_file
                    )
                    skill.add_module(module)

            for module_file in skill_dir.glob("*.json"):
                module = SkillModule(
                    name=module_file.stem,
                    path=module_file
                )
                skill.add_module(module)

            for module_file in skill_dir.glob("*.yaml"):
                if module_file.name not in ["config.yaml"]:
                    module = SkillModule(
                        name=module_file.stem,
                        path=module_file
                    )
                    skill.add_module(module)

            references_dir = skill_dir / "references"
            if references_dir.exists():
                for ref_file in references_dir.glob("*.md"):
                    module = SkillModule(
                        name=ref_file.stem,
                        path=ref_file
                    )
                    skill.add_module(module)

                for ref_file in references_dir.glob("*.json"):
                    module = SkillModule(
                        name=ref_file.stem,
                        path=ref_file
                    )
                    skill.add_module(module)

                for ref_file in references_dir.glob("*.yaml"):
                    if ref_file.name not in ["config.yaml"]:
                        module = SkillModule(
                            name=ref_file.stem,
                            path=ref_file
                        )
                        skill.add_module(module)

            return skill

        except Exception as e:
            logger.error(f"Failed to parse skill directory {skill_dir}: {e}")
            return None

    def _parse_skill_metadata(self, content: str) -> Dict[str, Any]:
        metadata = {}

        if content.startswith("---"):
            import yaml
            end_idx = content.find("---", 3)
            if end_idx != -1:
                yaml_content = content[3:end_idx].strip()
                try:
                    metadata = yaml.safe_load(yaml_content) or {}
                except yaml.YAMLError:
                    pass

        return metadata

    def _load_skill_config(self, skill_dir: Path) -> Dict[str, Any]:
        config_file = skill_dir / "config.yaml"
        if config_file.exists():
            try:
                import yaml
                return yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}
            except Exception as e:
                logger.warning(f"Failed to load skill config: {e}")

        return {}

    def list_available_skills(self) -> List[str]:
        if not self.skill_path.exists():
            return []

        skills = []
        for item in self.skill_path.iterdir():
            if item.is_dir() and (item / "SKILL.md").exists():
                skills.append(item.name)

        return skills

    def reload_skill(self, skill_name: str) -> Optional[Skill]:
        if skill_name in self._loaded_skills:
            del self._loaded_skills[skill_name]

        return self.load_skill(skill_name)


class MultiSkillLoader:
    """Load skills from multiple directories (core skills + business skills)"""

    def __init__(self, skill_paths: Optional[List[str]] = None):
        self.loaders: List[SkillLoader] = []
        self._skill_cache: Dict[str, Skill] = {}

        if skill_paths:
            for path in skill_paths:
                self.add_path(path)

    def add_path(self, skill_path: str) -> None:
        """Add a skill directory to search paths"""
        loader = SkillLoader(skill_path)
        self.loaders.append(loader)
        logger.info(f"Added skill path: {skill_path}")

    def load_skill(self, skill_name: str) -> Optional[Skill]:
        """Load a skill from any registered path"""
        if skill_name in self._skill_cache:
            return self._skill_cache[skill_name]

        for loader in self.loaders:
            skill = loader.load_skill(skill_name)
            if skill:
                self._skill_cache[skill_name] = skill
                logger.info(f"Loaded skill '{skill_name}' from {loader.skill_path}")
                return skill

        logger.error(f"Skill not found in any path: {skill_name}")
        return None

    def list_available_skills(self) -> Dict[str, List[str]]:
        """List all available skills from all paths"""
        result = {}
        for loader in self.loaders:
            skills = loader.list_available_skills()
            path_str = str(loader.skill_path)
            result[path_str] = skills

        return result

    def list_all_skills(self) -> List[str]:
        """Get a flat list of all available skills"""
        skills = set()
        for loader in self.loaders:
            skills.update(loader.list_available_skills())

        return sorted(list(skills))

    def reload_skill(self, skill_name: str) -> Optional[Skill]:
        """Reload a skill from all paths"""
        if skill_name in self._skill_cache:
            del self._skill_cache[skill_name]

        return self.load_skill(skill_name)

    def reload_all(self) -> None:
        """Reload all skills"""
        self._skill_cache.clear()
        for loader in self.loaders:
            loader._loaded_skills.clear()

    def get_skill_info(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed info about a skill"""
        skill = self.load_skill(skill_name)
        if not skill:
            return None

        return {
            "name": skill.name,
            "version": skill.version,
            "description": skill.description,
            "path": str(skill.skill_path),
            "modules": list(skill.modules.keys()),
            "scripts": skill.list_scripts(),
            "config_keys": list(skill.config.keys()) if skill.config else []
        }
