"""
Test script to validate core PRISM functionality before running the full application.
"""

import os
import config
import prism_logic
from agents import build_graph, create_initial_state
from langchain_openai import ChatOpenAI

def test_api_connection():
    """Test if we can connect to the OpenAI API."""
    print("Testing API connection...")
    
    if not config.OPENAI_API_KEY or config.OPENAI_API_KEY == "your_openai_api_key_here":
        print("❌ Please set your OPENAI_API_KEY in the .env file")
        return False
    
    try:
        llm = ChatOpenAI(
            model=config.OPENAI_MODEL,
            temperature=config.TEMPERATURE,
            api_key=config.OPENAI_API_KEY
        )
        
        # Simple test call
        from langchain_core.messages import HumanMessage
        response = llm.invoke([HumanMessage(content="Hello, this is a test. Please respond with 'Test successful'.")])
        print(f"✅ API connection successful: {response.content}")
        return True
        
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return False

def test_semantic_minimization():
    """Test the semantic minimization function."""
    print("\nTesting Semantic Minimization...")
    
    try:
        llm = ChatOpenAI(
            model=config.OPENAI_MODEL,
            temperature=config.TEMPERATURE,
            api_key=config.OPENAI_API_KEY
        )
        
        # Test input
        test_input = "I need a treatment plan and cost estimate. I have Diabetic Ketoacidosis (DKA) and I was prescribed RX_Alpha_7. My patient identifier is ID_12345."
        
        # Apply semantic minimization
        minimized = prism_logic.semantic_minimization_sm(test_input, llm)
        
        print(f"Original: {test_input}")
        print(f"Minimized: {minimized}")
        
        # Validate
        is_valid = prism_logic.validate_semantic_minimization(test_input, minimized)
        print(f"✅ Semantic minimization validation: {'PASSED' if is_valid else 'FAILED'}")
        
        return is_valid
        
    except Exception as e:
        print(f"❌ Semantic minimization test failed: {e}")
        return False

def test_graph_execution():
    """Test the LangGraph workflow execution."""
    print("\nTesting Graph Execution...")
    
    try:
        # Build graph
        graph = build_graph()
        
        # Test input
        test_secret = "I need a treatment plan and cost estimate. I have Diabetic Ketoacidosis (DKA) and I was prescribed RX_Alpha_7. My patient identifier is ID_12345."
        
        # Test BASELINE mode
        print("Testing BASELINE mode...")
        baseline_state = create_initial_state(test_secret, "BASELINE")
        baseline_result = graph.invoke(baseline_state)
        
        print(f"Baseline messages count: {len(baseline_result.get('messages', []))}")
        print(f"Baseline final output preview: {baseline_result.get('final_output', '')[:100]}...")
        
        # Test PRISM mode
        print("Testing PRISM mode...")
        prism_state = create_initial_state(test_secret, "PRISM")
        prism_result = graph.invoke(prism_state)
        
        print(f"PRISM messages count: {len(prism_result.get('messages', []))}")
        print(f"PRISM final output preview: {prism_result.get('final_output', '')[:100]}...")
        
        print("✅ Graph execution successful")
        return True
        
    except Exception as e:
        print(f"❌ Graph execution failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🔐 PRISM Framework - System Validation Tests")
    print("=" * 50)
    
    tests = [
        test_api_connection,
        test_semantic_minimization, 
        test_graph_execution
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("TEST SUMMARY:")
    print(f"Passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("✅ All tests passed! System is ready for full experiment.")
        print("\nTo run the full Streamlit application:")
        print("streamlit run main.py")
    else:
        print("❌ Some tests failed. Please check the configuration and try again.")
        print("\nMake sure you have:")
        print("1. Set OPENAI_API_KEY in the .env file")
        print("2. Internet connection for API calls")
        print("3. Sufficient API credits/quota")

if __name__ == "__main__":
    main()