"""Pytest configuration and fixtures"""

import os
import sys
from pathlib import Path
import tempfile
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest


@pytest.fixture(scope="session")
def project_root():
    """Get project root directory"""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def skills_dir(project_root):
    """Get skills directory"""
    return project_root / "skills"


@pytest.fixture(scope="session")
def fixtures_dir(project_root):
    """Get fixtures directory"""
    return project_root / "tests" / "fixtures"


@pytest.fixture
def temp_skill_dir():
    """Create a temporary skill directory for testing"""
    temp_dir = Path(tempfile.mkdtemp())
    skill_dir = temp_dir / "test_skill"
    skill_dir.mkdir()
    
    yield skill_dir
    
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_skill_content():
    """Sample SKILL.md content"""
    return """---
name: test-skill
version: "1.0.0"
description: "Test skill for unit testing"
license: MIT
---

# Test Skill

This is a test skill for unit testing purposes.
"""


@pytest.fixture
def sample_business_rules():
    """Sample business rules content"""
    return """---
name: business_rules
version: "1.0.0"
rules:
  - name: "field_naming"
    pattern: "field.*bracket"
    rule: "Use brackets for field names: [FieldName]"

  - name: "amount_conversion"
    pattern: "amount.*cast"
    rule: "Always CAST([Amount] AS FLOAT)"
---
"""


@pytest.fixture
def sample_metadata():
    """Sample metadata content"""
    return """```json
{
  "tables": {
    "users": {
      "columns": [
        {"name": "id", "type": "INTEGER"},
        {"name": "name", "type": "TEXT"},
        {"name": "age", "type": "INTEGER"}
      ]
    }
  }
}
```"""


@pytest.fixture
def sample_config():
    """Sample skill config"""
    return {
        "llm": {
            "provider": "openai",
            "model": "gpt-4",
            "api_key": "test-key",
            "temperature": 0.1,
            "max_tokens": 4096
        },
        "data_sources": [
            {
                "type": "excel",
                "enabled": True,
                "config": {
                    "max_preview_rows": 20
                }
            }
        ]
    }


@pytest.fixture
def mock_excel_file(fixtures_dir):
    """Create a mock Excel file for testing"""
    import pandas as pd
    
    data = {
        "id": [1, 2, 3],
        "name": ["Alice", "Bob", "Charlie"],
        "age": [25, 30, 35]
    }
    df = pd.DataFrame(data)
    
    excel_path = fixtures_dir / "test_data.xlsx"
    df.to_excel(excel_path, index=False, sheet_name="Sheet1")
    
    yield str(excel_path)
    
    if excel_path.exists():
        excel_path.unlink()
