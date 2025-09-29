"""
Core LangGraph State definition, Nodes, and Graph compilation.
Implements the three-agent workflow with state scrubbing capabilities.
"""

import sys
from typing import TypedDict, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
import operator
import config

# Python 3.8 compatibility for Annotated and Literal
if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal
import prism_logic
import llm_client


class AgentState(TypedDict):
    """
    Core shared memory that acts as the Reflection Log (target for adversarial probing).
    """
    # Core shared memory - the target for the Prober
    messages: Annotated[List[BaseMessage], operator.add]
    
    # User-defined, highly sensitive input (the SECRET to protect)
    full_secret_s: str
    
    # Non-sensitive "Unit of Meaningfulness" after Semantic Minimization
    sanitized_uom: str
    
    # Agent outputs
    final_output: str
    
    # Mode switch for experiment
    mode: Literal["BASELINE", "PRISM"]
    
    # Adversary's reconstruction attempt
    adversary_reconstruction: str
    
    # Utility success indicator
    task_success: bool
    
    # Additional tracking fields
    condition: str
    treatment_id: str
    patient_id: str


def input_encoder_sm(state: AgentState) -> AgentState:
    """
    Agent A (Input Encoder with Semantic Minimization)
    
    Critical implementation of State Scrubbing when mode == 'PRISM'.
    This is the core thesis contribution.
    """
    try:
        # Initialize LLM using unified client
        llm = llm_client.get_llm()
        
        user_input = state["full_secret_s"]
        mode = state["mode"]
        
        # Extract sensitive components
        condition, treatment_id, patient_id = prism_logic.extract_sensitive_components(user_input)
        
        if mode == "BASELINE":
            # BASELINE: Include raw sensitive data in message log (high leakage)
            prompt = config.AGENT_A_PROMPT.format(mode=mode, user_input=user_input)
            messages = [HumanMessage(content=prompt)]
            response = llm.invoke(messages)
            
            # Add FULL sensitive message to log (this will leak in baseline)
            agent_message = AIMessage(content=f"Agent A Analysis: {response.content}\nOriginal Input: {user_input}")
            
            return {
                **state,
                "messages": [agent_message],
                "sanitized_uom": user_input,  
                "condition": condition or "",
                "treatment_id": treatment_id or "",
                "patient_id": patient_id or ""
            }
            
        elif mode == "PRISM":
            # PRISM: Apply Semantic Minimization and State Scrubbing
            
            # Step 1: Perform Semantic Minimization
            sanitized_input = prism_logic.semantic_minimization_sm(user_input, llm)
            
            # Step 2: Process with Agent A using sanitized input
            prompt = config.AGENT_A_PROMPT.format(mode=mode, user_input=sanitized_input)
            messages = [HumanMessage(content=prompt)]
            response = llm.invoke(messages)
            
            # Step 3: CRITICAL - State Scrubbing
            # Only add NON-SENSITIVE message to the log
            agent_message = AIMessage(content=f"Agent A Analysis: {response.content}\nProcessed Input: {sanitized_input}")
            
            # Validate minimization was successful
            is_valid = prism_logic.validate_semantic_minimization(user_input, sanitized_input)
            if not is_valid:
                print(f"Warning: Semantic minimization may have failed for input: {user_input[:50]}...")
            
            return {
                **state,
                "messages": [agent_message],
                "sanitized_uom": sanitized_input,
                "condition": condition or "",
                "treatment_id": treatment_id or "",
                "patient_id": patient_id or ""
            }
    
    except Exception as e:
        print(f"Error in input_encoder_sm: {e}")
        # Fallback behavior
        return {
            **state,
            "messages": [AIMessage(content=f"Agent A Error: {str(e)}")],
            "sanitized_uom": state["full_secret_s"],
            "condition": "",
            "treatment_id": "",
            "patient_id": ""
        }


def treatment_agent(state: AgentState) -> AgentState:
    """
    Agent B (Treatment Advisor)
    
    Processes the available context (restricted by RI) and generates treatment recommendations.
    """
    try:
        # Initialize LLM using unified client
        llm = llm_client.get_llm()
        
        # Apply Restricted Information (RI) filtering
        filtered_state = prism_logic.restricted_information_ri(state, "Agent_B")
        
        # Get context from available messages
        context = "\n".join([msg.content for msg in filtered_state.get("messages", [])])
        treatment_id = state.get("treatment_id", "Unknown")
        
        # Generate treatment advice
        prompt = config.AGENT_B_PROMPT.format(
            context=context,
            treatment_id=treatment_id
        )
        
        messages = [HumanMessage(content=prompt)]
        response = llm.invoke(messages)
        
        # Add agent's response to message log
        agent_message = AIMessage(content=f"Agent B Treatment Advice: {response.content}")
        
        return {
            **state,
            "messages": state["messages"] + [agent_message]
        }
        
    except Exception as e:
        print(f"Error in treatment_agent: {e}")
        error_message = AIMessage(content=f"Agent B Error: {str(e)}")
        return {
            **state,
            "messages": state["messages"] + [error_message]
        }


def recomposition_agent(state: AgentState) -> AgentState:
    """
    Agent C (Pricing & Final Output)
    
    Provides final pricing and recommendations while maintaining privacy constraints.
    """
    try:
        # Initialize LLM using unified client
        llm = llm_client.get_llm()
        
        # Apply Restricted Information (RI) filtering
        filtered_state = prism_logic.restricted_information_ri(state, "Agent_C")
        
        # Get context from available messages
        context = "\n".join([msg.content for msg in filtered_state.get("messages", [])])
        treatment_id = state.get("treatment_id", "Unknown")
        
        # Generate final output with pricing
        prompt = config.AGENT_C_PROMPT.format(
            context=context,
            treatment_id=treatment_id
        )
        
        messages = [HumanMessage(content=prompt)]
        response = llm.invoke(messages)
        
        # Add agent's response to message log
        agent_message = AIMessage(content=f"Agent C Final Output: {response.content}")
        
        return {
            **state,
            "messages": state["messages"] + [agent_message],
            "final_output": response.content
        }
        
    except Exception as e:
        print(f"Error in recomposition_agent: {e}")
        error_message = AIMessage(content=f"Agent C Error: {str(e)}")
        return {
            **state,
            "messages": state["messages"] + [error_message],
            "final_output": f"Error in final processing: {str(e)}"
        }


def build_graph() -> StateGraph:
    """
    Build and compile the LangGraph workflow.
    
    Returns:
        StateGraph: Compiled graph ready for execution
    """
    # Create the workflow
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("Agent_A", input_encoder_sm)
    workflow.add_node("Agent_B", treatment_agent)
    workflow.add_node("Agent_C", recomposition_agent)
    
    # Define the flow: A → B → C
    workflow.set_entry_point("Agent_A")
    workflow.add_edge("Agent_A", "Agent_B")
    workflow.add_edge("Agent_B", "Agent_C")
    workflow.add_edge("Agent_C", END)
    
    # Compile the graph
    return workflow.compile()


def create_initial_state(full_secret: str, mode: Literal["BASELINE", "PRISM"]) -> AgentState:
    """
    Create initial state for the experiment.
    
    Args:
        full_secret: The complete sensitive user input
        mode: Experiment mode (BASELINE or PRISM)
        
    Returns:
        AgentState: Initial state for the workflow
    """
    return {
        "messages": [],
        "full_secret_s": full_secret,
        "sanitized_uom": "",
        "final_output": "",
        "mode": mode,
        "adversary_reconstruction": "",
        "task_success": False,
        "condition": "",
        "treatment_id": "",
        "patient_id": ""
    }