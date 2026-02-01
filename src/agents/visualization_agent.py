
from typing import TYPE_CHECKING, Dict, Any, List
import json
from langchain_core.messages import HumanMessage

from src.agents.llm import get_llm
from src.prompts.manager import render_prompt_template
from src.config.logger import LoggerManager

if TYPE_CHECKING:
    from workflow.graph import AgentState

VISUALIZATION_PROMPT = """
You are a data visualization expert.

Your task is to recommend the best chart type to visualize the provided data based on the user's query.

## User Query
{user_query}

## Data Sample (First 5 rows)
{data_sample}

## Instructions
1. Analyze the data and user intent.
2. Choose the most appropriate chart type from: bar, line, pie, scatter, area, or table.
3. Determine which columns should be on the X-axis (dimensions) and Y-axis (metrics).
4. Provide a title for the chart.

## Output Format
Return a JSON object with the following structure:
{{
  "chart_type": "bar|line|pie|scatter|area|table",
  "title": "Descriptive Chart Title",
  "config": {{
    "x_axis": "column_name_for_x",
    "y_axis": ["column_name_for_y1", "column_name_for_y2"],
    "series_names": ["Series 1 Name", "Series 2 Name"]
  }},
  "reasoning": "Explanation of why this chart type was chosen"
}}

If the data is not suitable for a chart (e.g., single value or too complex), set "chart_type" to "table".
"""

def visualization_node(state: "AgentState") -> "AgentState":
    """Visualization Node - Generates chart configuration based on data"""
    LoggerManager().info("Starting visualization_node")
    
    execution_data = state.get("execution_data")
    if not execution_data:
        LoggerManager().warning("No execution data available for visualization")
        return state

    user_query = state.get("user_query", "")
    
    # Take a sample of data
    data_sample = execution_data[:5]
    
    prompt = render_prompt_template(
        VISUALIZATION_PROMPT,
        user_query=user_query,
        data_sample=json.dumps(data_sample, ensure_ascii=False, indent=2)
    )
    
    llm = get_llm()
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content.replace("```json", "").replace("```", "").strip()
        
        chart_config = json.loads(content)
        state["chart_config"] = chart_config
        LoggerManager().info(f"Generated chart config: {chart_config}")
        
    except Exception as e:
        LoggerManager().error(f"Visualization generation failed: {e}")
        # Don't fail the workflow, just no chart
        state["chart_config"] = {"error": str(e)}

    return state
