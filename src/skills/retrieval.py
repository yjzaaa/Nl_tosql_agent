from typing import List, Dict, Any
from pathlib import Path
from langchain_core.tools import tool
from src.skills.loader import SkillLoader


class SkillRetriever:
    def __init__(self, skill_loader: SkillLoader):
        self.loader = skill_loader

    def search_skills(self, query: str) -> List[Dict[str, Any]]:
        """
        根据查询搜索相关技能。
        目前实现了基于名称和描述的简单关键词匹配。
        """
        results = []
        # 根据设置使用 MultiSkillLoader 或 SkillLoader
        # 目前假设我们在加载器的路径中搜索所有可用技能
        available_skills = self.loader.list_available_skills()

        query_terms = query.lower().split()

        for skill_name in available_skills:
            skill = self.loader.load_skill(skill_name)
            if not skill:
                continue

            score = 0
            # 简单关键词匹配
            text_to_search = (skill.name + " " + skill.description).lower()

            for term in query_terms:
                if term in text_to_search:
                    score += 1

            if score > 0:
                results.append(
                    {
                        "name": skill.name,
                        "description": skill.description,
                        "match_score": score,
                        "content": skill.get_business_rules(),  # 或者特定的模块内容
                    }
                )

        # 按分数排序
        results.sort(key=lambda x: x["match_score"], reverse=True)
        return results


@tool
def lookup_business_logic(query: str) -> str:
    """
    搜索与用户查询相关的业务逻辑和规则。
    当你需要在生成 SQL 之前了解特定的业务定义、计算方法或约束时，请使用此工具。
    """
    # 使用默认路径（或配置路径）初始化加载器
    loader = SkillLoader()
    retriever = SkillRetriever(loader)
    results = retriever.search_skills(query)

    if not results:
        return "未找到针对此查询的具体业务逻辑。"

    # 格式化前几个结果
    output = "找到相关业务逻辑：\n\n"
    for res in results[:3]:  # 取前3个
        output += f"--- 技能: {res['name']} ---\n"
        output += f"描述: {res['description']}\n"
        output += f"规则/内容: {res['content']}\n\n"

    return output
