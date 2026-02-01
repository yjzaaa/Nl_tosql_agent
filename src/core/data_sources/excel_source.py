from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
from .base import DataSourceStrategy
import sqlite3
import re

class ExcelDataSource(DataSourceStrategy):
    """Strategy for loading data from Excel files."""

    def __init__(self, file_path: str, sheet_name: Optional[str] = None):
        self.file_path = file_path
        self.sheet_name = sheet_name
        self.all_sheets: List[str] = []
        self._business_logic_context = ""
        self._common_questions_context = ""
        self._is_available = None
        self._loaded_df = None

    def load_data(self) -> pd.DataFrame:
        path = Path(self.file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {self.file_path}")

        if path.suffix.lower() not in [".xlsx", ".xls", ".xlsm"]:
            raise ValueError(f"不支持的文件格式: {path.suffix}")

        xlsx = pd.ExcelFile(self.file_path)
        self.all_sheets = xlsx.sheet_names

        self._load_context_sheets()

        target_sheet = self.sheet_name
        if target_sheet is None:
            data_sheets = [
                s for s in self.all_sheets if s not in ["解释和逻辑", "问题"]
            ]
            if data_sheets:
                target_sheet = data_sheets[0]
            else:
                target_sheet = self.all_sheets[0]
        elif target_sheet not in self.all_sheets:
            raise ValueError(
                f"工作表 '{target_sheet}' 不存在，可用工作表: {self.all_sheets}"
            )

        self.sheet_name = target_sheet
        self._loaded_df = pd.read_excel(self.file_path, sheet_name=target_sheet)
        return self._loaded_df

    def execute_query(self, query: str) -> pd.DataFrame:
        if self._loaded_df is None:
            self.load_data()

        conn = sqlite3.connect(":memory:")

        all_table_names = set()
        sheet_name = self.sheet_name
        all_table_names.add(sheet_name)

        clean_filename = (
            Path(self.file_path).stem
            .replace(" ", "_")
            .replace("-", "_")
        )
        if clean_filename and clean_filename[0].isdigit():
            clean_filename = f"df_{clean_filename}"
        all_table_names.add(clean_filename)

        try:
            from config.settings import get_config
            config = get_config()
            for key in config.excel.file_paths.keys():
                clean_key = key.replace(" ", "_").replace("-", "_")
                if clean_key and clean_key[0].isdigit():
                    clean_key = f"df_{clean_key}"
                all_table_names.add(clean_key)
                all_table_names.add(key)
        except Exception:
            pass

        self._loaded_df.to_sql(sheet_name, conn, index=False, if_exists="replace")
        if clean_filename != sheet_name:
            self._loaded_df.to_sql(clean_filename, conn, index=False, if_exists="replace")

        try:
            from core.loader.excel_loader import get_loader
            loader = get_loader()
            loaded_tables = loader.list_tables()

            for table_info in loaded_tables:
                table_id = table_info.get("id")
                t_loader = loader.get_table(table_id)
                if not t_loader or not t_loader.is_loaded:
                    continue

                df = t_loader.dataframe
                other_sheet_name = table_info.get("sheet_name", "")

                if other_sheet_name == sheet_name:
                    continue

                all_table_names.add(other_sheet_name)
                df.to_sql(other_sheet_name, conn, index=False, if_exists="replace")

                other_filename = Path(table_info.get("file_path", "unknown")).stem.replace(" ", "_").replace("-", "_")
                if other_filename and other_filename[0].isdigit():
                    other_filename = f"df_{other_filename}"
                if other_filename != other_sheet_name:
                    all_table_names.add(other_filename)
                    df.to_sql(other_filename, conn, index=False, if_exists="replace")
        except Exception:
            pass

        top_match = re.match(
            r"(?i)^\s*SELECT\s+TOP\s+(\d+)\s+(.+)", query, re.DOTALL
        )
        if top_match:
            limit_n = top_match.group(1)
            rest_query = top_match.group(2)
            query = f"SELECT {rest_query} LIMIT {limit_n}"

        result_df = pd.read_sql_query(query, conn)
        conn.close()
        return result_df

    def _load_context_sheets(self):
        try:
            if "解释和逻辑" in self.all_sheets:
                logic_df = pd.read_excel(self.file_path, sheet_name="解释和逻辑")
                if len(logic_df) > 20:
                    logic_df = logic_df.head(20)
                try:
                    self._business_logic_context = logic_df.to_markdown(index=False)
                except ImportError:
                    self._business_logic_context = logic_df.to_string(index=False)

            if "问题" in self.all_sheets:
                questions_df = pd.read_excel(self.file_path, sheet_name="问题")
                if len(questions_df) > 5:
                    questions_df = questions_df.head(5)
                try:
                    self._common_questions_context = questions_df.to_markdown(index=False)
                except ImportError:
                    self._common_questions_context = questions_df.to_string(index=False)
        except Exception as e:
            print(f"Warning: Failed to load context sheets: {e}")

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "source_type": "excel",
            "file_path": self.file_path,
            "filename": Path(self.file_path).name,
            "sheet_name": self.sheet_name,
            "all_sheets": self.all_sheets
        }

    def get_context(self) -> Dict[str, str]:
        return {
            "business_logic": self._business_logic_context,
            "common_questions": self._common_questions_context
        }

    def get_schema_info(self, table_names: List[str]) -> str:
        if self._loaded_df is None:
            self.load_data()
        cols = ", ".join([f"{c} ({self._loaded_df[c].dtype})" for c in self._loaded_df.columns])
        return f"表 {Path(self.file_path).name} ({self.sheet_name}) 列信息:\n  - {cols}"

    def is_available(self) -> bool:
        if self._is_available is None:
            self._is_available = Path(self.file_path).exists()
        return self._is_available
