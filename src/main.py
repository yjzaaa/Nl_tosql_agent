"""主入口模块 - 使用Skill-Aware工作流"""

import argparse
from dotenv import load_dotenv

from src.nl_to_sql_agent import NLToSQLAgent

load_dotenv()


def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(
        description="NL to SQL Agent - 智能查询助手",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--skill-path",
        "-s",
        type=str,
        default=None,
        help="Skills目录路径 (默认: ./skills)",
    )

    parser.add_argument(
        "--skill",
        type=str,
        default="nl-to-sql-agent",
        help="Skill名称 (默认: nl-to-sql-agent)",
    )

    parser.add_argument(
        "--query",
        "-q",
        type=str,
        default=None,
        help="直接执行查询",
    )

    parser.add_argument(
        "--list-skills",
        action="store_true",
        help="列出可用的skills",
    )

    parser.add_argument(
        "--cli",
        "-c",
        action="store_true",
        help="进入交互式命令行模式",
    )

    args = parser.parse_args()

    agent = NLToSQLAgent(skill_path=args.skill_path, skill_name=args.skill)

    if args.list_skills:
        skills = agent.list_available_skills()
        print("可用的skills:")
        for skill in skills:
            print(f"  - {skill}")
        return

    if args.query:
        result = agent.query(args.query)
        print(f"\n查询: {result['query']}")
        print(f"SQL: {result.get('sql', 'N/A')}")
        print(f"结果: {result.get('result', 'N/A')}")
        if result.get('error'):
            print(f"错误: {result['error']}")
        return

    if args.cli:
        run_cli(agent)
    else:
        parser.print_help()


def run_cli(agent: NLToSQLAgent):
    """运行交互式命令行模式"""
    print("=" * 50)
    print("NL to SQL Agent - 交互模式")
    print("=" * 50)
    print(f"当前Skill: {agent.skill_name}")
    print("输入 'exit' 或 'quit' 退出")
    print("=" * 50)

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n再见!")
            break

        if not user_input:
            continue

        if user_input.lower() in ["exit", "quit", "q"]:
            print("再见!")
            break

        try:
            result = agent.query(user_input)
            print(f"\nSQL: {result.get('sql', 'N/A')}")
            print(f"结果: {result.get('result', 'N/A')}")
            if result.get('error'):
                print(f"错误: {result['error']}")
        except Exception as e:
            print(f"\n处理出错: {e}")


if __name__ == "__main__":
    main()
