from pathlib import Path
import sys
import json
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.skills.middleware import get_skill_middleware
from src.skills.middleware.skill_middleware import SkillCatalogLoader
from src.agents.llm import get_llm



def main():
    repo_root = Path(__file__).resolve().parents[2]
    skill_path = repo_root / "skills"

    try:
        llm = get_llm()
    except Exception as exc:
        print(f"LLM not configured: {exc}")
        raise

    middleware = get_skill_middleware(
        skill_path=str(skill_path),
        default_skill="nl-to-sql-agent",
        llm=llm,
        confidence_threshold=0.1,
    )

    query = "预算 vs 实际对比，IT Allocation 近3个月趋势分析"
    catalog = SkillCatalogLoader(skill_path=str(skill_path))
    skill_list = [s.to_dict() for s in catalog.load_skill_summaries()]
    print("\n=== Skill Catalog (name/description) ===")
    print(json.dumps(skill_list, ensure_ascii=False, indent=2))
    print("======================================\n")

    result = middleware.run(query)

    print("\n=== Skill Middleware Business Test Output ===")
    print(json.dumps(str(result), ensure_ascii=False, indent=2))
    print("===========================================\n")

    print("\n=== Business Check Summary ===")
    print(f"Expected Skill: cost_allocation | Actual: {result.get('skill_name')}")
    print(f"Selected By: {result.get('skill_selected_by')}")
    print(f"Has Skill Context: {result.get('skill_context') is not None}")
    print(f"Has metadata module: {'metadata' in (result.get('skill_context') or {}).get('modules', {})}")
    print("==============================\n")


if __name__ == "__main__":
    main()
