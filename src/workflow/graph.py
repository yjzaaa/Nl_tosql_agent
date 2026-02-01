"""Workflow compatibility layer with absolute imports"""

# Use absolute imports to avoid circular dependencies
import sys
from pathlib import Path

# Add src to path if needed
if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

# Import new graph module using absolute path
from src.graph.graph import AgentState, GraphWorkflow

# Export for backward compatibility
__all__ = ["AgentState", "GraphWorkflow"]
