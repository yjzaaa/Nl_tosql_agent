"""日志接口实现 - 依赖倒置原则"""

import logging
import json
import re
from typing import Any, Dict, List, Optional, Union
from abc import ABC, abstractmethod

import colorama

colorama.init(autoreset=True)

from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.tree import Tree
from rich.syntax import Syntax
from rich.text import Text
from rich.theme import Theme
from rich import print as rprint

from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.outputs import LLMResult
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
    FunctionMessage,
    ChatMessage,
)


class LoggerManager:
    """日志管理器 - 实现 ILogger 接口"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not LoggerManager._initialized:
            self._setup_console()
            self._setup_color_maps()
            LoggerManager._initialized = True

    def _setup_console(self):
        """初始化 Rich 控制台"""
        CUSTOM_THEME = Theme(
            {
                "info": "dim cyan",
                "warning": "italic yellow",
                "error": "bold red",
                "success": "bold green",
                "debug": "dim blue",
                "user": "cyan",
                "ai": "green",
                "system": "yellow",
                "tool": "magenta",
            }
        )
        self.console = Console(
            force_terminal=True, color_system="auto", theme=CUSTOM_THEME
        )

    def _setup_color_maps(self):
        """配置颜色映射"""
        self.MESSAGE_COLORS = {
            "Human": ("[USER]", "cyan"),
            "AI": ("[ASSISTANT]", "green"),
            "System": ("[SYSTEM]", "yellow"),
            "Tool": ("[TOOL]", "magenta"),
            "Function": ("[FUNCTION]", "blue"),
            "Chat": ("[CHAT]", "white"),
            "default": ("[UNKNOWN]", "gray"),
        }

        self.STATUS_COLORS = {
            "running": ("[RUNNING]", "yellow"),
            "success": ("[SUCCESS]", "green"),
            "error": ("[ERROR]", "red"),
            "warning": ("[WARNING]", "yellow"),
            "pending": ("[PENDING]", "gray"),
        }

        self.RICH_MESSAGE_STYLES = {
            "Human": "cyan",
            "AI": "green",
            "System": "yellow",
            "Tool": "magenta",
            "Function": "blue",
            "Chat": "white",
            "default": "gray",
        }

        self.RICH_STATUS_STYLES = {
            "running": "yellow",
            "success": "green",
            "error": "red",
            "warning": "yellow",
            "pending": "gray",
        }

    def get_logger(self, name: str) -> logging.Logger:
        """获取 Logger 实例"""
        return logging.getLogger(name)

    def setup_logging(self, level: str = "INFO", enable_colors: bool = True):
        """配置全局日志"""
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        file_handler = logging.FileHandler(
            "excel_agent.log", mode="w", encoding="utf-8"
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(file_formatter)

        rich_handler = RichHandler(
            console=self.console,
            rich_tracebacks=True,
            show_path=False,
        )

        if enable_colors:
            logging.basicConfig(
                level=level,
                format="%(message)s",
                datefmt="[%X]",
                handlers=[rich_handler, file_handler],
            )
        else:
            logging.basicConfig(
                level=level,
                format="%(message)s",
                datefmt="[%X]",
                handlers=[file_handler],
            )

        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("openai").setLevel(logging.WARNING)

    def get_message_type_name(self, msg) -> str:
        """获取消息类型名称"""
        msg_type = type(msg).__name__
        type_map = {
            "HumanMessage": "Human",
            "AIMessage": "AI",
            "SystemMessage": "System",
            "ToolMessage": "Tool",
            "FunctionMessage": "Function",
            "ChatMessage": "Chat",
        }
        return type_map.get(msg_type, msg_type)

    def _strip_ansi(self, text: str) -> str:
        """移除 ANSI 转义码"""
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        return ansi_escape.sub("", text)

    def format_message_content(
        self, msg, max_lines: int = 15, max_chars: int = 1000
    ) -> str:
        """格式化消息内容"""
        content = ""

        if hasattr(msg, "content"):
            raw = msg.content
            if isinstance(raw, str):
                content = raw
            elif isinstance(raw, list):
                parts = []
                for item in raw[:10]:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            parts.append(item.get("text", ""))
                        elif item.get("type") == "tool_use":
                            parts.append(f"[Tool Call: {item.get('name', 'unknown')}]")
                            if "input" in item:
                                parts.append(str(item["input"])[:1000])
                    else:
                        parts.append(str(item))
                content = "\n".join(parts)
            else:
                content = str(raw)
        else:
            content = str(msg)

        if len(content) > max_chars:
            content = content[:max_chars] + "\n... (truncated)"

        lines = content.split("\n")
        if len(lines) > max_lines:
            content = "\n".join(lines[:max_lines]) + "\n... (truncated)"

        return content

    def info(self, message: str) -> None:
        """记录 info 级别日志"""
        logging.getLogger("info_logger").info(message)

    def warning(self, message: str) -> None:
        """记录 warning 级别日志"""
        logging.getLogger("info_logger").warning(message)

    def error(self, message: str) -> None:
        """记录 error 级别日志"""
        logging.getLogger("info_logger").error(message)

    def debug(self, message: str) -> None:
        """记录 debug 级别日志"""
        logging.getLogger("info_logger").debug(message)

    def log_separator(self, title: str = "", width: int = 80) -> None:
        """日志分隔线"""
        if title:
            content = f" {title} ".center(width - 2, "=")
        else:
            content = "=" * width
        msg = "\n" + content + "\n"
        print(msg)

    def _make_rich_panel(
        self,
        title: str,
        content: str,
        border_style: str = "blue",
        width: int = 80,
        title_style: str = "bold",
        content_style: str = "",
    ) -> Panel:
        """创建 Rich 面板（带颜色）

        Args:
            title: 面板标题（边框上显示）
            content: 面板内容
            border_style: 边框颜色样式
            width: 面板宽度
            title_style: 标题样式
            content_style: 内容样式（可指定颜色，如 "cyan", "green yellow" 等）
        """
        styled_title = Text(title, style=f"{title_style} {border_style}")

        if content_style:
            if content_style.startswith("code") or content_style.startswith("json"):
                styled_content = Syntax(
                    content,
                    content_style.split(":")[0] if ":" in content_style else "python",
                    theme="monokai",
                    word_wrap=True,
                )
            else:
                styled_content = Text(content, style=content_style)
        else:
            styled_content = Text(content)

        return Panel(
            styled_content,
            title=styled_title,
            border_style=border_style,
            width=width,
            expand=False,
        )

    def _make_type_panel(
        self, msg_type: str, content: str, border_style: str = "blue", width: int = 80
    ) -> Panel:
        """创建带消息类型的面板

        Args:
            msg_type: 消息类型（如 USER, ASSISTANT, SYSTEM 等）
            content: 面板内容
            border_style: 边框颜色样式
            width: 面板宽度
        """
        type_label = f"[{msg_type}]"
        styled_title = Text(type_label, style=f"bold {border_style}")
        styled_content = Text(content, style=border_style)

        return Panel(
            styled_content,
            title=styled_title,
            border_style=border_style,
            width=width,
            expand=False,
        )

    def _make_panel(self, title: str, content: str, width: int = 80) -> str:
        """创建纯文本面板（无 ANSI 码）"""
        border = "=" * (width - 2)
        title_line = f"= {title} "
        if len(title_line) < width - 1:
            title_line += " " * (width - 1 - len(title_line)) + "="
        else:
            title_line = "=" + title_line[: width - 2] + "="

        content_lines = content.split("\n")
        max_content_width = width - 4

        formatted_lines = [title_line]
        for line in content_lines:
            if len(line) > max_content_width:
                line = line[: max_content_width - 3] + "..."
            formatted_lines.append(f"| {line:<{max_content_width}} |")
        formatted_lines.append(f"|{border}|")

        return "\n".join(formatted_lines)

    def log_message_block(
        self, prefix: str, title: str, content: str, color: str = "blue"
    ) -> None:
        """日志消息块 - 自动应用颜色"""
        full_title = f"{prefix} {title}"
        panel = self._make_rich_panel(
            full_title,
            content,
            border_style=color,
            title_style="bold",
            content_style=color,
        )
        self.console.print(panel)

    def log_step(
        self, step_num: int, step_name: str, status: str, details: str = ""
    ) -> None:
        """日志步骤信息 - 自动应用颜色"""
        status_info = self.STATUS_COLORS.get(status, ("[?]", "white"))
        status_text = status_info[0]
        style = self.RICH_STATUS_STYLES.get(status, "white")

        lines = [
            f"Step {step_num}: {step_name}",
            f"Status: {status_text}",
        ]

        if details:
            detail_lines = details.split("\n")[:8]
            for line in detail_lines:
                indented = "    " + line
                if len(indented) > 76:
                    indented = indented[:73] + "..."
                lines.append(indented)
            if len(details.split("\n")) > 8:
                lines.append("    ... (truncated)")

        content = "\n".join(lines)
        panel = self._make_rich_panel(
            step_name,
            content,
            border_style=style,
            title_style="bold",
            content_style=style,
        )
        self.console.print(panel)

    def log_message_with_type(self, msg) -> None:
        """根据消息类型自动应用颜色并打印消息 - 边框显示消息类型"""
        msg_type = self.get_message_type_name(msg)
        style = self.RICH_MESSAGE_STYLES.get(msg_type, "gray")

        content = self.format_message_content(msg, max_lines=20, max_chars=1000)

        panel = self._make_type_panel(msg_type, content, border_style=style)
        self.console.print(panel)

    def log_workflow_step(
        self, step_name: str, description: str, status: str, extra_info: str = ""
    ) -> None:
        """通用工作流步骤日志输出 - 自动应用颜色"""
        status_info = self.STATUS_COLORS.get(status, ("[?]", "blue"))
        status_text = status_info[0]
        style = self.RICH_STATUS_STYLES.get(status, "blue")

        lines = [
            f"Step: {step_name}",
            f"Status: {status_text}",
            f"Description: {description}",
        ]

        if extra_info:
            lines.append(f"\n{extra_info}")

        content = "\n".join(lines)
        panel = self._make_rich_panel(
            step_name,
            content,
            border_style=style,
            title_style="bold",
            content_style=style,
        )
        self.console.print(panel)

    def log_sql_query(
        self, sql: str, status: str = "success", result_info: str = ""
    ) -> None:
        """SQL 查询日志输出 - 自动应用颜色"""
        status_text = "[SUCCESS]" if status == "success" else "[ERROR]"
        style = "green" if status == "success" else "red"

        content = f"SQL Query {status_text}\n\n{sql}"
        if result_info:
            content += f"\n\n{result_info}"

        panel = self._make_rich_panel(
            "SQL Query",
            content,
            border_style=style,
            title_style="bold",
            content_style="code:python",
        )
        self.console.print(panel)

    def log_result_table(
        self, title: str, headers: List[str], rows: List[List[Any]], max_rows: int = 10
    ) -> None:
        """结果表格日志输出 - 自动应用 Rich 表格颜色"""
        from rich.table import Table

        if not headers or not rows:
            panel = self._make_rich_panel(title, "No data", border_style="gray")
            self.console.print(panel)
            return

        table = Table(title=title, style="cyan", header_style="bold magenta")

        for h in headers:
            table.add_column(h)

        for row in rows[:max_rows]:
            table.add_row(*[str(val) for val in row])

        if len(rows) > max_rows:
            table.add_row(*["..." for _ in headers])

        self.console.print(table)

    def print_color(self, text: str, style: str = "info") -> None:
        """打印带颜色的文本"""
        rprint(f"[{style}]{text}[/{style}]")

    def print_table(
        self, data: list, headers: list = None, title: str = None, style: str = "info"
    ) -> None:
        """打印带颜色的表格"""
        from rich.table import Table

        table = Table(title=title, style=style)
        if headers:
            for h in headers:
                table.add_column(h)
        for row in data:
            table.add_row(*[str(c) for c in row])
        self.console.print(table)


_logger_manager = LoggerManager()


def get_logger(name: str) -> logging.Logger:
    """获取 Logger 实例 - 外界唯一入口"""
    return _logger_manager.get_logger(name)


def setup_logging(level: str = "INFO", enable_colors: bool = True):
    """配置全局日志"""
    return _logger_manager.setup_logging(level, enable_colors)


def get_logger_manager() -> LoggerManager:
    """获取 LoggerManager 实例"""
    return _logger_manager


def log_message_with_type(msg) -> None:
    """根据消息类型自动应用颜色并打印消息"""
    return _logger_manager.log_message_with_type(msg)


def log_step(step_num: int, step_name: str, status: str, details: str = "") -> None:
    """日志步骤信息 - 自动应用颜色"""
    return _logger_manager.log_step(step_num, step_name, status, details)


def log_workflow_step(
    step_name: str, description: str, status: str, extra_info: str = ""
) -> None:
    """通用工作流步骤日志输出"""
    return _logger_manager.log_workflow_step(step_name, description, status, extra_info)


def log_sql_query(sql: str, status: str = "success", result_info: str = "") -> None:
    """SQL 查询日志输出"""
    return _logger_manager.log_sql_query(sql, status, result_info)


def log_result_table(
    title: str, headers: List[str], rows: List[List[Any]], max_rows: int = 10
) -> None:
    """结果表格日志输出"""
    return _logger_manager.log_result_table(title, headers, rows, max_rows)


def log_message_block(
    prefix: str, title: str, content: str, color: str = "blue"
) -> None:
    """日志消息块"""
    return _logger_manager.log_message_block(prefix, title, content, color)


def log_separator(title: str = "", width: int = 80) -> None:
    """日志分隔线"""
    return _logger_manager.log_separator(title, width)


def print_color(text: str, style: str = "info") -> None:
    """打印带颜色的文本"""
    return _logger_manager.print_color(text, style)


def print_table(
    data: list, headers: list = None, title: str = None, style: str = "info"
) -> None:
    """打印带颜色的表格"""
    return _logger_manager.print_table(data, headers, title, style)


def get_message_type_name(msg) -> str:
    """获取消息类型名称"""
    return _logger_manager.get_message_type_name(msg)


def format_message_content(msg, max_lines: int = 15, max_chars: int = 500) -> str:
    """格式化消息内容"""
    return _logger_manager.format_message_content(msg, max_lines, max_chars)
