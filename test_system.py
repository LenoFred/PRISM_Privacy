"""
Test script to validate core PRISM functionality before running the full application.
"""

import os
import config
import prism_logic
import llm_client
import metrics
import agents
from agents import build_graph, create_initial_state

def test_api_connection():
    """Test if we can connect to the LLM API."""
    print("Testing API connection...")
    
    # Check provider configuration
    provider = config.LLM_PROVIDER.lower()
    if provider == "openai":
        if not config.OPENAI_API_KEY or config.OPENAI_API_KEY == "your_openai_api_key_here":
            print("❌ Please set your OPENAI_API_KEY in the .env file")
            return False
    elif provider == "hf":
        if not config.HF_TOKEN or config.HF_TOKEN == "your_hf_token_here":
            print("❌ Please set your HF_TOKEN in the .env file")
            return False
    
    try:
        llm = llm_client.get_llm()
        
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
        # LLM will be created automatically in semantic_minimization_sm
        
        # Test input
        test_input = "I need a treatment plan and cost estimate. I have Diabetic Ketoacidosis (DKA) and I was prescribed RX_Alpha_7. My patient identifier is ID_12345."
        
        # Apply semantic minimization
        minimized = prism_logic.semantic_minimization_sm(test_input)
        
        print(f"Original: {test_input}")
        print(f"Minimized: {minimized}")
        
        # Validate
        is_valid = prism_logic.validate_semantic_minimization(test_input, minimized)
        print(f"✅ Semantic minimization validation: {'PASSED' if is_valid else 'FAILED'}")
        
        return is_valid
        
    except Exception as e:
        print(f"❌ Semantic minimization test failed: {e}")
        return False

def test_restricted_information():
    """Test the Restricted Information (RI) access control."""
    print("\nTesting Restricted Information (RI) Access Control...")
    
    try:
        # Create a mock state with all possible fields
        full_state = {
            "full_secret_s": "I need a treatment plan and cost estimate. I have Diabetic Ketoacidosis (DKA) and I was prescribed RX_Alpha_7. My patient identifier is ID_12345.",
            "sanitized_uom": "I need a treatment plan and cost estimate. I have Chronic Ailment Category and I was prescribed RX_Alpha_7. My patient identifier is PID_Hashed.",
            "messages": [],
            "final_output": "Treatment plan ready",
            "mode": "PRISM",
            "task_success": True,
            "adversary_reconstruction": "",
            "sensitive_data": "This should not be accessible"
        }
        
        # Test Agent_A access (should only see basic operational fields)
        agent_a_state = prism_logic.restricted_information_ri(full_state, "Agent_A")
        agent_a_allowed = set(config.AGENT_ACL.get("Agent_A", []))
        agent_a_actual = set(agent_a_state.keys()) - {"mode", "final_output", "task_success", "adversary_reconstruction"}
        
        # Test Agent_B access
        agent_b_state = prism_logic.restricted_information_ri(full_state, "Agent_B")
        agent_b_allowed = set(config.AGENT_ACL.get("Agent_B", []))
        agent_b_actual = set(agent_b_state.keys()) - {"mode", "final_output", "task_success", "adversary_reconstruction"}
        
        # Test Agent_C access
        agent_c_state = prism_logic.restricted_information_ri(full_state, "Agent_C")
        agent_c_allowed = set(config.AGENT_ACL.get("Agent_C", []))
        agent_c_actual = set(agent_c_state.keys()) - {"mode", "final_output", "task_success", "adversary_reconstruction"}
        
        # Validate access control
        access_violations = []
        
        if not agent_a_actual.issubset(agent_a_allowed):
            access_violations.append(f"Agent_A has unauthorized access: {agent_a_actual - agent_a_allowed}")
        
        if not agent_b_actual.issubset(agent_b_allowed):
            access_violations.append(f"Agent_B has unauthorized access: {agent_b_actual - agent_b_allowed}")
            
        if not agent_c_actual.issubset(agent_c_allowed):
            access_violations.append(f"Agent_C has unauthorized access: {agent_c_actual - agent_c_allowed}")
        
        # Check that sensitive_data is not accessible to any agent
        if "sensitive_data" in agent_a_state or "sensitive_data" in agent_b_state or "sensitive_data" in agent_c_state:
            access_violations.append("Sensitive data leaked to agents")
        
        if access_violations:
            print(f"❌ Access control violations: {'; '.join(access_violations)}")
            return False
        else:
            print("✅ Restricted Information (RI) access control: PASSED")
            return True
            
    except Exception as e:
        print(f"❌ Restricted Information test failed: {e}")
        return False

def test_adversary_prober():
    """Test the adversarial prober functionality."""
    print("\nTesting Adversary Prober...")
    
    try:
        from langchain_core.messages import AIMessage
        
        # Create a state with sensitive information in messages (BASELINE scenario)
        baseline_state = {
            "messages": [
                AIMessage(content="Processing patient with Diabetic Ketoacidosis (DKA), ID_12345"),
                AIMessage(content="Recommended treatment: RX_Alpha_7"),
                AIMessage(content="Final pricing calculated for patient ID_12345")
            ],
            "full_secret_s": "I need a treatment plan for Diabetic Ketoacidosis (DKA), patient ID_12345",
            "mode": "BASELINE"
        }
        
        # Run adversarial probe
        reconstruction = metrics.run_adversary_prober(baseline_state)
        
        # Extract ground truth components
        condition, treatment_id, patient_id = prism_logic.extract_sensitive_components(baseline_state["full_secret_s"])
        
        # Check if adversary successfully reconstructed sensitive info
        exfiltration_success = metrics.calculate_exfiltration_success(reconstruction, condition, patient_id)
        
        print(f"Ground truth: {condition}, {patient_id}")
        print(f"Adversary reconstruction: {reconstruction}")
        print(f"Exfiltration successful: {exfiltration_success}")
        
        # Test with PRISM state (should have less sensitive info)
        prism_state = {
            "messages": [
                AIMessage(content="Processing patient with Chronic Ailment Category, PID_Hashed"),
                AIMessage(content="Recommended treatment: RX_Alpha_7"),
                AIMessage(content="Final pricing calculated for patient PID_Hashed")
            ],
            "full_secret_s": "I need a treatment plan for Diabetic Ketoacidosis (DKA), patient ID_12345",
            "mode": "PRISM"
        }
        
        prism_reconstruction = metrics.run_adversary_prober(prism_state)
        prism_exfiltration = metrics.calculate_exfiltration_success(prism_reconstruction, condition, patient_id)
        
        print(f"PRISM adversary reconstruction: {prism_reconstruction}")
        print(f"PRISM exfiltration successful: {prism_exfiltration}")
        
        print("✅ Adversary prober test: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Adversary prober test failed: {e}")
        return False

def test_task_success_evaluation():
    """Test the task success evaluation functionality."""
    print("\nTesting Task Success Evaluation...")
    
    try:
        # Get LLM instance for testing
        llm = agents.get_llm()
        
        # Test successful output
        successful_output = "Based on your Chronic Ailment Category, I recommend continuing with RX_Alpha_7. The estimated cost is $150."
        success_result = metrics.evaluate_task_success(successful_output, "RX_Alpha_7", llm)
        
        # Test unsuccessful output (missing treatment)
        unsuccessful_output = "I cannot provide specific treatment recommendations."
        failure_result = metrics.evaluate_task_success(unsuccessful_output, "RX_Alpha_7", llm)
        
        print(f"Successful output evaluation: {success_result}")
        print(f"Unsuccessful output evaluation: {failure_result}")
        
        if success_result and not failure_result:
            print("✅ Task success evaluation: PASSED")
            return True
        else:
            print("❌ Task success evaluation: FAILED")
            return False
            
    except Exception as e:
        print(f"❌ Task success evaluation test failed: {e}")
        return False

def test_sensitive_component_extraction():
    """Test extraction of sensitive components from user input."""
    print("\nTesting Sensitive Component Extraction...")
    
    try:
        test_input = "I need a treatment plan and cost estimate. I have Diabetic Ketoacidosis (DKA) and I was prescribed RX_Alpha_7. My patient identifier is ID_12345."
        
        condition, treatment_id, patient_id = prism_logic.extract_sensitive_components(test_input)
        
        expected_condition = "Diabetic Ketoacidosis (DKA)"
        expected_treatment = "RX_Alpha_7"
        expected_patient_id = "ID_12345"
        
        print(f"Extracted - Condition: {condition}, Treatment: {treatment_id}, Patient ID: {patient_id}")
        
        if (condition == expected_condition and 
            treatment_id == expected_treatment and 
            patient_id == expected_patient_id):
            print("✅ Sensitive component extraction: PASSED")
            return True
        else:
            print("❌ Sensitive component extraction: FAILED")
            return False
            
    except Exception as e:
        print(f"❌ Sensitive component extraction test failed: {e}")
        return False

def test_unit_of_meaningfulness():
    """Test the creation of Unit of Meaningfulness (UoM)."""
    print("\nTesting Unit of Meaningfulness Creation...")
    
    try:
        # Test UoM creation
        condition = "Diabetic Ketoacidosis (DKA)"
        treatment_id = "RX_Alpha_7"
        patient_id = "ID_12345"
        
        uom = prism_logic.create_unit_of_meaningfulness(condition, treatment_id, patient_id)
        
        print(f"Original components: {condition}, {treatment_id}, {patient_id}")
        print(f"Unit of Meaningfulness: {uom}")
        
        # Validate UoM properties
        # Should not contain original sensitive info
        if condition in uom or patient_id in uom:
            print("❌ UoM contains sensitive information")
            return False
        
        # Should contain treatment ID for utility
        if treatment_id not in uom:
            print("❌ UoM missing treatment ID (utility loss)")
            return False
        
        # Should contain generic categories
        if "Chronic Ailment Category" not in uom or "PID_Hashed" not in uom:
            print("❌ UoM missing expected generic terms")
            return False
        
        print("✅ Unit of Meaningfulness creation: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Unit of Meaningfulness test failed: {e}")
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
    print("🔐 PRISM Framework - Comprehensive System Validation Tests")
    print("=" * 60)
    
    # Core functionality tests
    core_tests = [
        ("API Connection", test_api_connection),
        ("Semantic Minimization", test_semantic_minimization),
        ("Restricted Information", test_restricted_information),
        ("Sensitive Component Extraction", test_sensitive_component_extraction),
        ("Unit of Meaningfulness", test_unit_of_meaningfulness),
    ]
    
    # Advanced functionality tests 
    advanced_tests = [
        ("Adversary Prober", test_adversary_prober),
        ("Task Success Evaluation", test_task_success_evaluation),
        ("Graph Execution", test_graph_execution),
    ]
    
    all_results = []
    
    print("\n📋 CORE FUNCTIONALITY TESTS")
    print("-" * 40)
    core_results = []
    for test_name, test_func in core_tests:
        print(f"\n🔧 {test_name}:")
        try:
            result = test_func()
            core_results.append(result)
            all_results.append(result)
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            core_results.append(False)
            all_results.append(False)
    
    print(f"\nCore Tests Summary: {sum(core_results)}/{len(core_results)} passed")
    
    print("\n🚀 ADVANCED FUNCTIONALITY TESTS")
    print("-" * 40)
    advanced_results = []
    for test_name, test_func in advanced_tests:
        print(f"\n🔬 {test_name}:")
        try:
            result = test_func()
            advanced_results.append(result)
            all_results.append(result)
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            advanced_results.append(False)
            all_results.append(False)
    
    print(f"\nAdvanced Tests Summary: {sum(advanced_results)}/{len(advanced_results)} passed")
    
    print("\n" + "=" * 60)
    print("🎯 FINAL TEST SUMMARY:")
    print(f"Core Functionality: {sum(core_results)}/{len(core_results)} passed")
    print(f"Advanced Functionality: {sum(advanced_results)}/{len(advanced_results)} passed")
    print(f"Overall: {sum(all_results)}/{len(all_results)} passed")
    
    if all(all_results):
        print("\n✅ ALL TESTS PASSED! 🎉")
        print("🚀 PRISM Framework is fully validated and ready for experimentation.")
        print("\nTo run the full Streamlit application:")
        print("   streamlit run main.py")
        print("\nTo run specific module tests:")
        print("   python -c \"import metrics; metrics.test_adversary_prober()\"")
        print("   python -c \"import metrics; metrics.test_task_success_evaluation()\"")
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("🔧 Please check the configuration and resolve issues before proceeding.")
        
        # Provide specific guidance based on which tests failed
        if not all(core_results):
            print("\n🚨 CORE FUNCTIONALITY ISSUES:")
            failed_core = [name for (name, _), result in zip(core_tests, core_results) if not result]
            for failed in failed_core:
                print(f"   - {failed}")
        
        if not all(advanced_results):
            print("\n⚠️  ADVANCED FUNCTIONALITY ISSUES:")
            failed_advanced = [name for (name, _), result in zip(advanced_tests, advanced_results) if not result]
            for failed in failed_advanced:
                print(f"   - {failed}")
        
        print("\n📋 TROUBLESHOOTING CHECKLIST:")
        print("1. ✅ Set your LLM API key in the .env file:")
        print("   - For OpenAI: Set OPENAI_API_KEY and LLM_PROVIDER=openai")
        print("   - For HuggingFace: Set HF_TOKEN and LLM_PROVIDER=hf")
        print("2. ✅ Verify internet connection for API calls")
        print("3. ✅ Check sufficient API credits/quota")
        print("4. ✅ Ensure all dependencies are installed: pip install -r requirements.txt")
        print("5. ✅ Verify .env file is in the correct directory")

if __name__ == "__main__":
    main()