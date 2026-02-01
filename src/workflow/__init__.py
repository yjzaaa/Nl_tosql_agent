"""Workflow compatibility layer"""

# Import new graph module with absolute imports
import sys
from pathlib import Path

# Add src to path if needed
if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from graph.graph
from src.graph.graph import AgentState, GraphWorkflow

# Define get_graph function that returns a new instance
def get_graph(skill=None):
    """Get workflow graph instance
    
    Args:
        skill: Optional skill configuration to apply
        
    Returns:
        GraphWorkflow instance
    """
    return GraphWorkflow()

# Create a default instance
_default_workflow = GraphWorkflow()

# Export for backward compatibility
__all__ = ["AgentState", "GraphWorkflow", "get_graph"]

# Also export get_graph_function for alternative naming
get_graph_function = get_graph
