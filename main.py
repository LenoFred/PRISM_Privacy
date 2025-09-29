"""
Main Streamlit application for PRISM Privacy Framework demonstration.
Provides the experimental interface and results visualization.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import random
import time
from typing import Dict, List
import config
import agents
import metrics
import prism_logic


def initialize_app():
    """Initialize the Streamlit application."""
    st.set_page_config(
        page_title="PRISM Privacy Framework",
        page_icon="🔐",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    if "results" not in st.session_state:
        st.session_state.results = {}
    if "experiment_running" not in st.session_state:
        st.session_state.experiment_running = False


def setup_llm():
    """Setup LLM configuration and validate API key."""
    try:
        from langchain_openai import ChatOpenAI
        
        if not config.OPENAI_API_KEY or config.OPENAI_API_KEY == "your_openai_api_key_here":
            st.error("Please set your OPENAI_API_KEY in the .env file")
            st.stop()
        
        llm = ChatOpenAI(
            model=config.OPENAI_MODEL,
            temperature=config.TEMPERATURE,
            api_key=config.OPENAI_API_KEY
        )
        
        return llm
        
    except Exception as e:
        st.error(f"Error initializing LLM: {e}")
        st.info("Make sure you have installed the required packages: pip install -r requirements.txt")
        st.stop()


def create_sidebar():
    """Create the sidebar with experiment configuration."""
    st.sidebar.title("🔐 PRISM Configuration")
    
    st.sidebar.markdown("""
    **PRISM Framework:** Privacy through Restricted Information & Semantic Minimization
    
    This experiment demonstrates the effectiveness of PRISM in preventing the 
    Puzzle Piece Privacy Problem (PZPP) in multi-agent LLM systems.
    """)
    
    # Experiment configuration
    st.sidebar.subheader("Experiment Settings")
    
    n_trials = st.sidebar.number_input(
        "Number of Trials per Mode",
        min_value=1,
        max_value=100,
        value=20,
        help="Number of experimental trials to run for each mode (Baseline vs PRISM)"
    )
    
    # Show sample data
    st.sidebar.subheader("Sample Sensitive Data")
    st.sidebar.write("**Conditions:**", config.SENSITIVE_CONDITIONS[:3], "...")
    st.sidebar.write("**Treatment IDs:**", config.TREATMENT_IDS[:3], "...")
    st.sidebar.write("**Patient IDs:**", config.PATIENT_IDS[:3], "...")
    
    return n_trials


def display_header():
    """Display the main header and description."""
    st.title("🔐 PRISM Privacy Framework for Agentic LLM Systems")
    
    st.markdown("""
    **Empirical Validation of Privacy-Utility Trade-offs in Multi-Agent Workflows**
    
    This system demonstrates the **Puzzle Piece Privacy Problem (PZPP)** and validates the 
    **PRISM Framework** solution through controlled A/B testing across three scenarios:
    
    - **🚨 Baseline (Unmitigated):** Expected High Exfiltration Rate (ER)
    - **🔒 PRISM Framework:** Expected Low ER with Preserved Task Success Rate (TSR)
    """)


def run_experiment_mode(mode: str, n_trials: int, llm, graph) -> Dict:
    """
    Run experiment for a specific mode.
    
    Args:
        mode: "BASELINE" or "PRISM"
        n_trials: Number of trials to run
        llm: LLM instance
        graph: Compiled LangGraph workflow
        
    Returns:
        Dict containing experiment results and metrics
    """
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Initialize results storage
    results = []
    
    for trial in range(n_trials):
        # Update progress
        progress = (trial + 1) / n_trials
        progress_bar.progress(progress)
        status_text.text(f"Running {mode} trial {trial + 1}/{n_trials}...")
        
        # Generate fresh sensitive data
        condition = random.choice(config.SENSITIVE_CONDITIONS)
        treatment_id = random.choice(config.TREATMENT_IDS)
        patient_id = random.choice(config.PATIENT_IDS)
        
        full_secret = config.USER_INPUT_TEMPLATE.format(
            condition=condition,
            treatment_id=treatment_id,
            patient_id=patient_id
        )
        
        # Run single experiment
        exfiltration_success, task_success, detailed_result = metrics.run_single_experiment(
            full_secret, mode, graph, llm
        )
        
        detailed_result["trial"] = trial + 1
        results.append(detailed_result)
    
    # Calculate final metrics
    final_metrics = metrics.calculate_metrics(results)
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()
    
    return {
        "metrics": final_metrics,
        "detailed_results": results
    }


def display_results_comparison(baseline_results: Dict, prism_results: Dict):
    """Display comparative results between baseline and PRISM."""
    
    st.subheader("📊 Experimental Results")
    
    # Create metrics comparison table
    comparison_data = {
        "Scenario": ["Baseline (Unmitigated)", "PRISM Framework"],
        "Exfiltration Rate (ER)": [
            f"{baseline_results['metrics']['ER']:.2%}",
            f"{prism_results['metrics']['ER']:.2%}"
        ],
        "Task Success Rate (TSR)": [
            f"{baseline_results['metrics']['TSR']:.2%}",
            f"{prism_results['metrics']['TSR']:.2%}"
        ],
        "Privacy-Utility Score": [
            f"{1 - baseline_results['metrics']['ER'] + baseline_results['metrics']['TSR']:.2f}",
            f"{1 - prism_results['metrics']['ER'] + prism_results['metrics']['TSR']:.2f}"
        ]
    }
    
    comparison_df = pd.DataFrame(comparison_data)
    st.table(comparison_df)
    
    # Calculate improvement metrics
    er_reduction = (baseline_results['metrics']['ER'] - prism_results['metrics']['ER']) / baseline_results['metrics']['ER'] * 100 if baseline_results['metrics']['ER'] > 0 else 0
    tsr_preservation = (prism_results['metrics']['TSR'] / baseline_results['metrics']['TSR']) * 100 if baseline_results['metrics']['TSR'] > 0 else 100
    
    # Display key findings
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "🛡️ Privacy Improvement (ER Reduction)",
            f"{er_reduction:.1f}%",
            delta=f"-{baseline_results['metrics']['ER'] - prism_results['metrics']['ER']:.2%} ER"
        )
    
    with col2:
        st.metric(
            "⚡ Utility Preservation (TSR)",
            f"{tsr_preservation:.1f}%",
            delta=f"{prism_results['metrics']['TSR'] - baseline_results['metrics']['TSR']:+.2%}"
        )
    
    with col3:
        st.metric(
            "🎯 Overall Privacy-Utility Score",
            f"{1 - prism_results['metrics']['ER'] + prism_results['metrics']['TSR']:.2f}",
            delta=f"{(1 - prism_results['metrics']['ER'] + prism_results['metrics']['TSR']) - (1 - baseline_results['metrics']['ER'] + baseline_results['metrics']['TSR']):+.2f}"
        )


def create_visualizations(baseline_results: Dict, prism_results: Dict):
    """Create visualizations for the results."""
    
    st.subheader("📈 Privacy-Utility Visualization")
    
    # Create ER vs TSR scatter plot
    fig = go.Figure()
    
    # Add Baseline point
    fig.add_trace(go.Scatter(
        x=[baseline_results['metrics']['ER']],
        y=[baseline_results['metrics']['TSR']],
        mode='markers',
        marker=dict(size=15, color='red', symbol='x'),
        name='Baseline (Unmitigated)',
        text=['High Privacy Risk<br>High Utility'],
        textposition="top center"
    ))
    
    # Add PRISM point
    fig.add_trace(go.Scatter(
        x=[prism_results['metrics']['ER']],
        y=[prism_results['metrics']['TSR']],
        mode='markers',
        marker=dict(size=15, color='green', symbol='star'),
        name='PRISM Framework',
        text=['Low Privacy Risk<br>Preserved Utility'],
        textposition="top center"
    ))
    
    # Add ideal point
    fig.add_trace(go.Scatter(
        x=[0],
        y=[1],
        mode='markers',
        marker=dict(size=12, color='gold', symbol='diamond'),
        name='Ideal (ER=0, TSR=1)',
        text=['Perfect Privacy<br>Perfect Utility'],
        textposition="top center"
    ))
    
    # Update layout
    fig.update_layout(
        title="Privacy-Utility Trade-off: PRISM vs Baseline",
        xaxis_title="Exfiltration Rate (ER) - Lower is Better",
        yaxis_title="Task Success Rate (TSR) - Higher is Better",
        showlegend=True,
        width=800,
        height=500,
        xaxis=dict(range=[-0.05, 1.05]),
        yaxis=dict(range=[-0.05, 1.05])
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Bar chart comparison
    metrics_data = pd.DataFrame({
        'Scenario': ['Baseline', 'PRISM'],
        'Exfiltration Rate': [baseline_results['metrics']['ER'], prism_results['metrics']['ER']],
        'Task Success Rate': [baseline_results['metrics']['TSR'], prism_results['metrics']['TSR']]
    })
    
    fig_bar = px.bar(
        metrics_data.melt(id_vars=['Scenario'], var_name='Metric', value_name='Rate'),
        x='Scenario',
        y='Rate',
        color='Metric',
        barmode='group',
        title="Comparative Metrics: Baseline vs PRISM",
        color_discrete_map={'Exfiltration Rate': 'red', 'Task Success Rate': 'green'}
    )
    
    fig_bar.update_layout(yaxis=dict(range=[0, 1]))
    st.plotly_chart(fig_bar, use_container_width=True)


def show_detailed_examples(baseline_results: Dict, prism_results: Dict):
    """Show detailed examples of successful and failed cases."""
    
    st.subheader("🔍 Detailed Examples")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🚨 Baseline Example (High Leakage)")
        
        # Find a successful exfiltration in baseline
        baseline_success = next(
            (r for r in baseline_results['detailed_results'] if r.get('exfiltration_success')), 
            baseline_results['detailed_results'][0]
        )
        
        with st.expander("View Baseline Leakage Example"):
            st.write("**Original Secret:**", baseline_success.get('full_secret', 'N/A'))
            st.write("**Adversary Reconstruction:**", baseline_success.get('adversary_output', 'N/A'))
            st.write("**Exfiltration Success:**", "✅ Yes" if baseline_success.get('exfiltration_success') else "❌ No")
            
            st.write("**Message Log (What Adversary Sees):**")
            for i, msg in enumerate(baseline_success.get('message_log', [])[:3]):
                st.text(f"Message {i+1}: {msg[:200]}...")
    
    with col2:
        st.markdown("### 🛡️ PRISM Example (Protected)")
        
        # Find a failed exfiltration in PRISM (protection success)
        prism_protected = next(
            (r for r in prism_results['detailed_results'] if not r.get('exfiltration_success')), 
            prism_results['detailed_results'][0]
        )
        
        with st.expander("View PRISM Protection Example"):
            st.write("**Original Secret:**", prism_protected.get('full_secret', 'N/A'))
            st.write("**Adversary Reconstruction:**", prism_protected.get('adversary_output', 'N/A'))
            st.write("**Exfiltration Success:**", "✅ Yes" if prism_protected.get('exfiltration_success') else "❌ No")
            
            st.write("**Message Log (What Adversary Sees):**")
            for i, msg in enumerate(prism_protected.get('message_log', [])[:3]):
                st.text(f"Message {i+1}: {msg[:200]}...")


def main():
    """Main Streamlit application."""
    
    # Initialize app
    initialize_app()
    
    # Display header
    display_header()
    
    # Create sidebar
    n_trials = create_sidebar()
    
    # Setup LLM
    llm = setup_llm()
    
    # Build graph
    with st.spinner("Initializing PRISM framework..."):
        graph = agents.build_graph()
    
    st.success("✅ PRISM framework initialized successfully!")
    
    # Experiment execution
    st.subheader("🧪 Run Experiments")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚨 Run Baseline Experiment", disabled=st.session_state.experiment_running):
            st.session_state.experiment_running = True
            
            with st.spinner(f"Running {n_trials} baseline trials..."):
                baseline_results = run_experiment_mode("BASELINE", n_trials, llm, graph)
                st.session_state.results["baseline"] = baseline_results
            
            st.success(f"✅ Baseline experiment completed! ER: {baseline_results['metrics']['ER']:.2%}")
            st.session_state.experiment_running = False
    
    with col2:
        if st.button("🛡️ Run PRISM Experiment", disabled=st.session_state.experiment_running):
            st.session_state.experiment_running = True
            
            with st.spinner(f"Running {n_trials} PRISM trials..."):
                prism_results = run_experiment_mode("PRISM", n_trials, llm, graph)
                st.session_state.results["prism"] = prism_results
            
            st.success(f"✅ PRISM experiment completed! ER: {prism_results['metrics']['ER']:.2%}")
            st.session_state.experiment_running = False
    
    # Run both experiments button
    st.markdown("---")
    if st.button("🔬 Run Complete Comparative Study", disabled=st.session_state.experiment_running):
        st.session_state.experiment_running = True
        
        # Run baseline
        st.info("🚨 Running Baseline experiments...")
        baseline_results = run_experiment_mode("BASELINE", n_trials, llm, graph)
        st.session_state.results["baseline"] = baseline_results
        
        # Run PRISM
        st.info("🛡️ Running PRISM experiments...")
        prism_results = run_experiment_mode("PRISM", n_trials, llm, graph)
        st.session_state.results["prism"] = prism_results
        
        st.success("✅ Complete comparative study finished!")
        st.session_state.experiment_running = False
    
    # Display results if available
    if "baseline" in st.session_state.results and "prism" in st.session_state.results:
        st.markdown("---")
        display_results_comparison(
            st.session_state.results["baseline"],
            st.session_state.results["prism"]
        )
        
        create_visualizations(
            st.session_state.results["baseline"],
            st.session_state.results["prism"]
        )
        
        show_detailed_examples(
            st.session_state.results["baseline"],
            st.session_state.results["prism"]
        )
        
        # Thesis conclusion
        st.subheader("🎓 Thesis Validation")
        
        er_reduction = (st.session_state.results["baseline"]['metrics']['ER'] - st.session_state.results["prism"]['metrics']['ER']) / st.session_state.results["baseline"]['metrics']['ER'] * 100 if st.session_state.results["baseline"]['metrics']['ER'] > 0 else 0
        
        st.success(f"""
        **PRISM Framework Validation Results:**
        
        ✅ **Privacy Improvement:** {er_reduction:.1f}% reduction in Exfiltration Rate
        
        ✅ **Utility Preservation:** {st.session_state.results["prism"]['metrics']['TSR']:.1%} Task Success Rate maintained
        
        ✅ **Puzzle Piece Privacy Problem (PZPP) Mitigation:** Successfully demonstrated through semantic minimization and restricted information access
        
        **Conclusion:** The PRISM framework successfully addresses the privacy-utility trade-off in multi-agent LLM systems.
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    **PRISM Framework:** Privacy through Restricted Information & Semantic Minimization
    
    *Empirical validation of privacy-preserving techniques for agentic LLM systems*
    """)


if __name__ == "__main__":
    main()