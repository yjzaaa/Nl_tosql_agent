"""Skill Middleware - LangChain Runnable + ReAct Agent for Skill selection."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableLambda
from src.core.llm import get_llm
from src.skills.loader import SkillLoader


@dataclass
class SkillSummary:
    name: str
    description: str
    version: str = ""
    path: str = ""
    license: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
        }


@dataclass
class SkillContext:
    skill: Dict[str, Any]
    skill_doc: str
    modules: Dict[str, str]
    config: Dict[str, Any]
    scripts: List[Dict[str, Any]]
    script_contents: Dict[str, str]
    references: List[str]


class SkillCatalogLoader:
    def __init__(self, skill_path: Optional[str] = None):
        self.skill_path = Path(skill_path) if skill_path else Path.cwd() / "skills"

    def load_skill_summaries(self) -> List[SkillSummary]:
        summaries: List[SkillSummary] = []
        if not self.skill_path.exists():
            return summaries

        for item in self.skill_path.iterdir():
            if not item.is_dir():
                continue
            skill_md = item / "SKILL.md"
            if not skill_md.exists():
                continue
            summary = self._parse_skill_md(skill_md)
            if summary:
                summaries.append(summary)

        return summaries

    def _parse_skill_md(self, skill_md: Path) -> Optional[SkillSummary]:
        content = skill_md.read_text(encoding="utf-8")
        front_matter = self._parse_front_matter(content)

        name = front_matter.get("name") or skill_md.parent.name
        description = front_matter.get("description", "")
        version = front_matter.get("version", "")
        license_name = front_matter.get("license", "")

        return SkillSummary(
            name=name,
            description=description,
            version=version,
            path=str(skill_md.parent),
            license=license_name,
        )

    def _parse_front_matter(self, content: str) -> Dict[str, Any]:
        if not content.startswith("---"):
            return {}

        end_idx = content.find("---", 3)
        if end_idx == -1:
            return {}

        raw = content[3:end_idx].strip()
        if not raw:
            return {}

        try:
            import yaml

            data = yaml.safe_load(raw) or {}
            return data if isinstance(data, dict) else {}
        except Exception:
            return self._parse_front_matter_fallback(raw)

    @staticmethod
    def _parse_front_matter_fallback(raw: str) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        for line in raw.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip().strip("\"")
        return data


class SkillContextLoader:
    def __init__(self, skill_path: Optional[str] = None):
        self.loader = SkillLoader(skill_path)

    def load(self, skill_name: str) -> Optional[SkillContext]:
        skill = self.loader.load_skill(skill_name)
        if not skill:
            return None

        skill_doc = ""
        if skill.skill_path:
            skill_md = Path(skill.skill_path) / "SKILL.md"
            if skill_md.exists():
                skill_doc = skill_md.read_text(encoding="utf-8")

        modules: Dict[str, str] = {}
        for name, module in skill.modules.items():
            modules[name] = module.load_content()

        references = sorted(list(modules.keys()))

        scripts = skill.list_scripts()
        script_contents: Dict[str, str] = {}
        for item in scripts:
            script_path = item.get("path")
            script_name = item.get("name") or script_path
            if script_path:
                try:
                    script_contents[script_name] = Path(script_path).read_text(
                        encoding="utf-8"
                    )
                except Exception:
                    script_contents[script_name] = ""

        return SkillContext(
            skill={
                "name": skill.name,
                "version": skill.version,
                "description": skill.description,
                "license": skill.license,
            },
            skill_doc=skill_doc,
            modules=modules,
            config=skill.config or {},
            scripts=scripts,
            script_contents=script_contents,
            references=references,
        )


class SkillSelectorReActAgent:
    def __init__(
        self,
        skill_path: Optional[str] = None,
        llm=None,
        default_skill: str = "nl-to-sql-agent",
        confidence_threshold: float = 0.4,
    ):
        self.catalog = SkillCatalogLoader(skill_path)
        self.default_skill = default_skill
        self.confidence_threshold = confidence_threshold
        self.llm = llm

    @staticmethod
    def _parse_selection(text: str) -> Optional[Dict[str, Any]]:
        cleaned = text.replace("```json", "").replace("```", "").strip()
        try:
            data = json.loads(cleaned)
            if isinstance(data, dict) and data.get("skill_name"):
                return data
        except Exception:
            pass

        match = re.search(r"skill_name\s*[:=]\s*['\"]?([\w\-]+)", cleaned)
        if match:
            return {"skill_name": match.group(1), "confidence": 0.5}

        return None

    def select(self, user_query: str) -> Dict[str, Any]:
        if not self.llm:
            return {"skill_name": self.default_skill, "confidence": 0.0}

        summaries = self.catalog.load_skill_summaries()
        payload = [s.to_dict() for s in summaries]

        system_prompt = (
            "你是一个技能选择助手。请根据用户问题与技能列表选择最匹配的技能。"
            "技能列表是一个数组，每个元素包含 name 与 description。"
            "只返回 JSON：{\"skill_name\":\"...\", \"confidence\":0.0, \"reasoning_summary\":\"...\"}"
        )
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content=(
                    "用户问题:\n"
                    f"{user_query}\n\n"
                    "技能列表(JSON):\n"
                    f"{json.dumps(payload, ensure_ascii=False)}"
                )
            ),
        ]

        response = self.llm.invoke(messages)
        selection = self._parse_selection(response.content)

        if not selection:
            return {"skill_name": self.default_skill, "confidence": 0.0}

        if selection.get("confidence", 0.0) < self.confidence_threshold:
            selection["skill_name"] = self.default_skill

        return selection


class SkillMiddleware:
    def __init__(
        self,
        skill_path: Optional[str] = None,
        default_skill: str = "nl-to-sql-agent",
        llm=None,
        confidence_threshold: float = 0.4,
    ):
        self.skill_path = skill_path
        self.default_skill = default_skill
        self.confidence_threshold = confidence_threshold
        self.llm = llm

        self.selector = SkillSelectorReActAgent(
            skill_path=skill_path,
            llm=llm,
            default_skill=default_skill,
            confidence_threshold=confidence_threshold,
        )
        self.context_loader = SkillContextLoader(skill_path)

    def run(self, user_query: str) -> Dict[str, Any]:
        selection = self.selector.select(user_query)
        skill_name = selection.get("skill_name")
        confidence = selection.get("confidence", 0.0)

        context = self.context_loader.load(skill_name) if skill_name else None
        skill_obj = self.context_loader.loader.load_skill(skill_name) if skill_name else None

        selected_by = "react_agent" if self.llm else "heuristic"
        if confidence < self.confidence_threshold:
            selected_by = "fallback"

        return {
            "skill": skill_obj,
            "skill_name": skill_name,
            "skill_context": context.__dict__ if context else None,
            "skill_selected_by": selected_by,
            "skill_confidence": confidence,
        }

    def as_runnable(self) -> RunnableLambda:
        return RunnableLambda(lambda input_data: self.run(input_data.get("user_query", "")))


_skill_middleware_instance: Optional[SkillMiddleware] = None


def get_skill_middleware_singleton(
    skill_path: Optional[str] = None,
    default_skill: str = "nl-to-sql-agent",
    llm=None,
    confidence_threshold: float = 0.4,
) -> SkillMiddleware:
    global _skill_middleware_instance
    if _skill_middleware_instance is None:
        _skill_middleware_instance = SkillMiddleware(
            skill_path=skill_path,
            default_skill=default_skill,
            llm=llm or get_llm(),
            confidence_threshold=confidence_threshold,
        )
    return _skill_middleware_instance


def select_skill_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Workflow node: select skill and inject skill context into state."""
    user_query = state.get("user_query") or ""
    middleware = get_skill_middleware_singleton(
        skill_path=None,
        default_skill=state.get("skill_name") or "nl-to-sql-agent",
    )

    result = middleware.run(user_query)
    state["skill"] = result.get("skill")
    state["skill_name"] = result.get("skill_name")
    state["skill_context"] = result.get("skill_context")
    state["skill_selected_by"] = result.get("skill_selected_by")
    state["skill_confidence"] = result.get("skill_confidence")

    return state


def get_skill_middleware(
    skill_path: Optional[str] = None,
    default_skill: str = "nl-to-sql-agent",
    llm=None,
    confidence_threshold: float = 0.4,
) -> SkillMiddleware:
    """Factory for SkillMiddleware."""
    return SkillMiddleware(
        skill_path=skill_path,
        default_skill=default_skill,
        llm=llm or get_llm(),
        confidence_threshold=confidence_threshold,
    )
