#!/usr/bin/env python
"""
运行测试脚本

使用方法:
    python run_tests.py                    # 运行所有测试
    python run_tests.py --coverage          # 运行测试并生成覆盖率报告
    python run_tests.py --watch             # 监听模式
    python run_tests.py --file test_file   # 运行特定文件
"""

import sys
import subprocess
from pathlib import Path


def run_pytest(args):
    """运行pytest命令"""
    cmd = ["python", "-m", "pytest"] + args
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    return result.returncode


def main():
    args = sys.argv[1:]

    if not args:
        return run_pytest(["-v"])

    if "--help" in args or "-h" in args:
        print(__doc__)
        return 0

    pytest_args = []

    if "--coverage" in args or "-c" in args:
        pytest_args.extend([
            "--cov=src",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-report=xml"
        ])

    if "--watch" in args or "-w" in args:
        pytest_args.append("--watch")

    if "--verbose" in args or "-v" in args:
        pytest_args.append("-vv")

    if "--file" in args or "-f" in args:
        try:
            idx = args.index("--file") + 1 if "--file" in args else args.index("-f") + 1
            file_path = args[idx]
            pytest_args.append(file_path)
        except IndexError:
            print("Error: --file requires a file path")
            return 1

    if "--slow" not in args and "-s" not in args:
        pytest_args.append("-m")
        pytest_args.append("not slow")

    return run_pytest(pytest_args)


if __name__ == "__main__":
    sys.exit(main())
