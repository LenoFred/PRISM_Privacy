"""
Core PRISM Mechanism Implementation
Contains the two core thesis contributions: Semantic Minimization (SM) and Restricted Information (RI)
"""

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import config


def semantic_minimization_sm(prompt: str, llm: ChatOpenAI) -> str:
    """
    SM Component: Semantic Minimization
    
    Uses an LLM call to perform prompt-aware transformation.
    Redacts specific sensitive information while preserving utility.
    
    Args:
        prompt: The initial sensitive user prompt (containing P1, P2, P3)
        llm: The LLM instance for performing the transformation
        
    Returns:
        str: A fragmented string that preserves utility but breaks semantic linkage
    """
    try:
        # Create the semantic minimization prompt
        minimization_prompt = config.SEMANTIC_MINIMIZATION_PROMPT.format(
            original_query=prompt
        )
        
        # Invoke LLM for semantic transformation
        messages = [HumanMessage(content=minimization_prompt)]
        response = llm.invoke(messages)
        
        # Extract the minimized content
        minimized_content = response.content.strip()
        
        return minimized_content
        
    except Exception as e:
        print(f"Error in semantic minimization: {e}")
        # Fallback: basic redaction if LLM fails
        return _fallback_minimization(prompt)


def restricted_information_ri(state: Dict[str, Any], agent_key: str) -> Dict[str, Any]:
    """
    RI Component: Restricted Information
    
    Enforces the Principle of Least Privilege on the LangGraph state.
    Returns a filtered version of the state based on pre-defined ACL.
    
    Args:
        state: The full AgentState including cumulative log
        agent_key: The key of the next agent (e.g., 'Agent_B')
        
    Returns:
        dict: Filtered state based on access control list
    """
    # Get allowed fields for this agent
    allowed_fields = config.AGENT_ACL.get(agent_key, [])
    
    # Create filtered state
    filtered_state = {}
    
    for field in allowed_fields:
        if field in state:
            filtered_state[field] = state[field]
    
    # Always include non-sensitive operational fields
    operational_fields = ["mode", "final_output", "task_success", "adversary_reconstruction"]
    for field in operational_fields:
        if field in state:
            filtered_state[field] = state[field]
    
    return filtered_state


def _fallback_minimization(prompt: str) -> str:
    """
    Fallback minimization if LLM fails.
    Uses simple pattern matching to redact sensitive information.
    """
    # Simple pattern-based redaction
    minimized = prompt
    
    # Replace specific conditions with generic categories
    for condition in config.SENSITIVE_CONDITIONS:
        if condition in minimized:
            minimized = minimized.replace(condition, "Chronic Ailment Category")
    
    # Replace specific patient IDs with generic hash
    for patient_id in config.PATIENT_IDS:
        if patient_id in minimized:
            minimized = minimized.replace(patient_id, "PID_Hashed")
    
    return minimized


def extract_sensitive_components(user_input: str) -> tuple:
    """
    Extract the three sensitive components (P1, P2, P3) from user input.
    
    Returns:
        tuple: (condition, treatment_id, patient_id)
    """
    condition = None
    treatment_id = None
    patient_id = None
    
    # Extract condition (P1)
    for cond in config.SENSITIVE_CONDITIONS:
        if cond in user_input:
            condition = cond
            break
    
    # Extract treatment ID (P2)
    for treatment in config.TREATMENT_IDS:
        if treatment in user_input:
            treatment_id = treatment
            break
    
    # Extract patient ID (P3)
    for pid in config.PATIENT_IDS:
        if pid in user_input:
            patient_id = pid
            break
    
    return condition, treatment_id, patient_id


def validate_semantic_minimization(original: str, minimized: str) -> bool:
    """
    Validate that semantic minimization was successful.
    
    Returns:
        bool: True if sensitive info was properly minimized
    """
    # Check that specific conditions are not present
    for condition in config.SENSITIVE_CONDITIONS:
        if condition in minimized:
            return False
    
    # Check that specific patient IDs are not present
    for patient_id in config.PATIENT_IDS:
        if patient_id in minimized:
            return False
    
    # Check that treatment IDs are still present (utility preservation)
    has_treatment = any(treatment in minimized for treatment in config.TREATMENT_IDS)
    
    return has_treatment


def create_unit_of_meaningfulness(condition: str, treatment_id: str, patient_id: str) -> str:
    """
    Create a Unit of Meaningfulness (UoM) that preserves utility while breaking semantic linkage.
    
    Args:
        condition: Original medical condition
        treatment_id: Treatment identifier (preserved for utility)
        patient_id: Patient identifier (to be anonymized)
        
    Returns:
        str: Unit of Meaningfulness preserving utility but not privacy-sensitive linkage
    """
    # Map specific conditions to general categories
    condition_mapping = {
        "Diabetic Ketoacidosis (DKA)": "Chronic Ailment Category",
        "Acute Myocardial Infarction": "Cardiovascular Condition",
        "Severe Bipolar Disorder": "Mental Health Condition",
        "Advanced Parkinson's Disease": "Neurological Condition",
        "Chronic Kidney Disease Stage 4": "Renal Condition",
        "Multiple Sclerosis Relapse": "Autoimmune Condition",
        "Severe Depression Episode": "Mental Health Condition",
        "Acute Pancreatitis": "Digestive System Condition",
        "Rheumatoid Arthritis Flare": "Autoimmune Condition",
        "Severe Asthma Exacerbation": "Respiratory Condition"
    }
    
    # Get generic category
    generic_condition = condition_mapping.get(condition, "Medical Condition")
    
    # Create non-invertible patient identifier
    hashed_patient_id = "PID_Hashed"
    
    # Construct UoM preserving utility (treatment_id) but breaking linkage
    uom = f"I need a treatment plan and cost estimate. I have {generic_condition} and I was prescribed {treatment_id}. My patient identifier is {hashed_patient_id}."
    
    return uom