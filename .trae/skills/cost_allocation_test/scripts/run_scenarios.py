"""
Script to run the cost allocation scenarios test.
Usage: python run_scenarios.py
"""

import sys
import os
import pytest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[4]  # .trae/skills/cost_allocation_test/scripts -> root
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.nl_to_sql_agent import NLToSQLAgent
from src.core.data_sources.manager import get_data_source_manager

def run_test_q1(agent):
    print("\n=== Test Q1: IT Services ===")
    query = "What services do IT cost include in FY24? And what is the allocation key?"
    try:
        response = agent.query(query, data_source_type="postgresql", recursion_limit=50)
        print(f"SQL: {response.get('sql')}")
        print(f"Result: {response.get('result')}")
        if response["success"]:
            print("✅ Q1 Passed")
        else:
            print(f"❌ Q1 Failed: {response.get('error')}")
    except Exception as e:
        print(f"❌ Q1 Exception: {e}")

def run_test_q2(agent):
    print("\n=== Test Q2: HR Budget ===")
    query = "What was the HR Cost in FY26 Budget1?"
    try:
        response = agent.query(query, data_source_type="postgresql", recursion_limit=50)
        print(f"SQL: {response.get('sql')}")
        print(f"Result: {response.get('result')}")
        if response["success"]:
            print("✅ Q2 Passed")
        else:
            print(f"❌ Q2 Failed: {response.get('error')}")
    except Exception as e:
        print(f"❌ Q2 Exception: {e}")

def run_test_q3(agent):
    print("\n=== Test Q3: IT Allocation ===")
    query = "What was the actual IT cost allocated to CT in FY25?"
    try:
        response = agent.query(query, data_source_type="postgresql", recursion_limit=50)
        print(f"SQL: {response.get('sql')}")
        print(f"Result: {response.get('result')}")
        if response["success"]:
            print("✅ Q3 Passed")
        else:
            print(f"❌ Q3 Failed: {response.get('error')}")
    except Exception as e:
        print(f"❌ Q3 Exception: {e}")

def run_test_q4(agent):
    print("\n=== Test Q4: Procurement Change ===")
    query = "How does Procurement Cost change from FY25 Actual to FY26 Budget1?"
    try:
        response = agent.query(query, data_source_type="postgresql", recursion_limit=50)
        print(f"SQL: {response.get('sql')}")
        print(f"Result: {response.get('result')}")
        if response["success"]:
            print("✅ Q4 Passed")
        else:
            print(f"❌ Q4 Failed: {response.get('error')}")
    except Exception as e:
        print(f"❌ Q4 Exception: {e}")

def run_test_q5(agent):
    print("\n=== Test Q5: HR Allocation Change ===")
    query = "How is the change of HR allocation to 413001 between FY26 Budget1 and FY25 Actual?"
    try:
        response = agent.query(query, data_source_type="postgresql", recursion_limit=50)
        print(f"SQL: {response.get('sql')}")
        print(f"Result: {response.get('result')}")
        if response["success"]:
            print("✅ Q5 Passed")
        else:
            print(f"❌ Q5 Failed: {response.get('error')}")
    except Exception as e:
        print(f"❌ Q5 Exception: {e}")

def main():
    print("Initializing Test Environment...")
    
    # Setup Data Source
    manager = get_data_source_manager()
    if "postgresql" not in manager.list_available_strategies():
        print("❌ PostgreSQL strategy not detected.")
        return
        
    manager.set_strategy("postgresql")
    if not manager.is_available():
        print("❌ PostgreSQL connection failed.")
        return
        
    print("✅ PostgreSQL Connected")
    
    # Initialize Agent
    agent = NLToSQLAgent(skill_name="cost_allocation")
    print("✅ Agent Initialized with 'cost_allocation' skill")
    
    # Run Tests
    run_test_q1(agent)
    run_test_q2(agent)
    run_test_q3(agent)
    run_test_q4(agent)
    run_test_q5(agent)

if __name__ == "__main__":
    main()
