"""
Human-in-the-Loop: How LangGraph interrupt() really works

Key concepts:
1. interrupt() PAUSES the workflow - stream stops returning events
2. To RESUME, you must use Command.resume() with the user's response
3. Without resume, the workflow stays frozen forever
"""

from langchain_core.tools import tool as create_tool
from langgraph.graph import StateGraph, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Annotated, List
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    user_query: str
    result: str
    sql_query: str


@create_tool
def execute_sql(query: str) -> str:
    """Execute SQL after human approval."""
    interrupt_info = {
        "description": "SQL execution requires your confirmation",
        "action_request": {"action": "execute_sql", "args": {"query": query}},
    }
    response = interrupt(interrupt_info)

    if response is None:
        raise ValueError("Interrupted without response")

    action = response.get("action", "accept")

    if action == "accept":
        return f"EXECUTED: {query}"
    elif action == "edit":
        edited = response.get("args", {}).get("query", query)
        return f"EXECUTED (edited): {edited}"
    elif action == "respond":
        return f"USER FEEDBACK: {response.get('feedback', '')}"
    else:
        raise ValueError(f"Unknown action: {action}")


def execute_node(state: AgentState) -> AgentState:
    result = execute_sql.invoke({"query": state["sql_query"]})
    return {**state, "result": result}


from langgraph.checkpoint.memory import MemorySaver


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("generate", lambda s: {**s, "sql_query": f"SELECT * FROM ({s['user_query']})"})
    g.add_node("execute", execute_node)
    g.set_entry_point("generate")
    g.add_edge("generate", "execute")
    g.add_edge("execute", END)
    return g.compile(checkpointer=MemorySaver())


def test_scenario_1_accept():
    """Scenario 1: User accepts - workflow continues normally"""
    print("\n" + "=" * 50)
    print("SCENARIO 1: User accepts SQL")
    print("=" * 50)

    graph = build_graph()
    initial = {"messages": [], "user_query": "Show users", "result": "", "sql_query": ""}
    config = {"configurable": {"thread_id": "test-1"}}

    print("\n[Step 1] Starting workflow...")
    print("[Step 2] Workflow runs until interrupt() is called...")

    events = []
    for event in graph.stream(initial, config=config):
        events.append(event)
        for node, state in event.items():
            print(f"  [{node}]")

    print(f"\n[Step 3] Workflow PAUSED at __interrupt__")
    print(f"  Total events so far: {len(events)}")
    print("  The stream STOPPED - nothing more will come out until resumed!")

    print("\n[Step 4] User reviews and accepts via Command.resume()...")
    resume_command = Command(resume={"action": "accept", "args": {}})

    print("[Step 5] Resuming workflow with user's response...")
    for event in graph.stream(resume_command, config=config):
        for node, state in event.items():
            print(f"  [{node}] result: {state.get('result', 'N/A')[:50]}...")

    print("\n[Result] Workflow completed successfully!")


def test_scenario_2_edit():
    """Scenario 2: User edits SQL - workflow continues with edited query"""
    print("\n" + "=" * 50)
    print("SCENARIO 2: User edits SQL")
    print("=" * 50)

    graph = build_graph()
    initial = {"messages": [], "user_query": "Show users", "result": "", "sql_query": ""}
    config = {"configurable": {"thread_id": "test-2"}}

    print("\n[Step 1] Starting workflow...")
    for event in graph.stream(initial, config=config):
        for node, _ in event.items():
            print(f"  [{node}]")
        if "__interrupt__" in event:
            print("  --> Workflow PAUSED")

    print("\n[Step 2] User edits the SQL...")
    print("  Original: SELECT * FROM (Show users)")
    print("  Edited:   SELECT id, name FROM users LIMIT 10")

    resume_command = Command(resume={
        "action": "edit",
        "args": {"query": "SELECT id, name FROM users LIMIT 10"}
    })

    print("[Step 3] Resuming with edited query...")
    for event in graph.stream(resume_command, config=config):
        for node, state in event.items():
            if "result" in state:
                print(f"  [{node}] result: {state['result']}")

    print("\n[Result] Executed the EDITED query!")


def test_scenario_3_respond():
    """Scenario 3: User responds without executing"""
    print("\n" + "=" * 50)
    print("SCENARIO 3: User provides feedback, no execution")
    print("=" * 50)

    graph = build_graph()
    initial = {"messages": [], "user_query": "Show users", "result": "", "sql_query": ""}
    config = {"configurable": {"thread_id": "test-3"}}

    print("\n[Step 1] Workflow paused at interrupt...")
    for event in graph.stream(initial, config=config):
        if "__interrupt__" in event:
            print("  --> Workflow PAUSED")

    print("\n[Step 2] User provides feedback instead of executing...")
    resume_command = Command(resume={
        "action": "respond",
        "feedback": "This query is wrong, please check the table name"
    })

    print("[Step 3] Resuming with user's feedback...")
    for event in graph.stream(resume_command, config=config):
        for node, state in event.items():
            if "result" in state:
                print(f"  [{node}] result: {state['result']}")

    print("\n[Result] Returned user's feedback, SQL was NOT executed!")


if __name__ == "__main__":
    print("=" * 50)
    print("LangGraph Human-in-the-Loop Demonstration")
    print("=" * 50)
    print("\nThis demo shows how interrupt() + Command.resume() works.")
    print("No mocking - real LangGraph interrupt behavior!")

    # test_scenario_1_accept()
    test_scenario_2_edit()
    # test_scenario_3_respond()

    print("\n" + "=" * 50)
    print("KEY INSIGHT:")
    print("  - interrupt() stops the stream")
    print("  - Workflow is FROZEN until Command.resume() is called")
    print("  - In real apps: frontend calls resume when user clicks a button")
    print("=" * 50)
