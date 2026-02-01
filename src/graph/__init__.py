"""Graph-based Workflow Definition"""

from .graph import AgentState, GraphWorkflow

__all__ = ["AgentState", "GraphWorkflow"]

"""Graph module - Export classes and get_graph function"""

from .graph import AgentState, GraphWorkflow

# Create a default instance for convenience
_default_workflow = None

def get_graph(skill=None):
    """Get workflow graph instance
    
    Args:
        skill: Optional skill configuration to apply
        
    Returns:
        GraphWorkflow instance
    """
    global _default_workflow
    if skill:
        _default_workflow = GraphWorkflow()
    else:
        if _default_workflow is None:
            _default_workflow = GraphWorkflow()
    return _default_workflow

__all__ = ["AgentState", "GraphWorkflow", "get_graph"]
