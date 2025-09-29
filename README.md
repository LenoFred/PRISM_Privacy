# PRISM Privacy Framework - Empirical Validation

## Overview

This project implements the **PRISM (Privacy through Restricted Information & Semantic Minimization) Framework** to address the **Puzzle Piece Privacy Problem (PZPP)** in multi-agent LLM systems.

### Core Problem: Puzzle Piece Privacy Problem (PZPP)
Individual agent outputs may seem non-sensitive/secured, but when combined across multiple agents, they can reveal sensitive information through cumulative leakage in reflection logs.

### Solution: PRISM Framework
- **Restricted Information (RI)**: Enforces access control through LangGraph state schema
- **Semantic Minimization (SM)**: Transforms sensitive inputs into privacy-preserving "Units of Meaningfulness"

## Project Structure

```
prism_experiment/
├── main.py              # Streamlit interface and experiment runner
├── agents.py            # LangGraph state definition and agent nodes
├── metrics.py           # ER and TSR calculation functions
├── config.py            # Configuration and data templates
├── prism_logic.py       # Core PRISM mechanism (RI + SM)
├── requirements.txt     # Python dependencies
├── .env                 # API keys (create from template)
└── README.md           # This file
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

Create a `.env` file with your OpenAI API key:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo
TEMPERATURE=0.1
```

### 3. Run the Application

```bash
streamlit run main.py
```

### 4. Run Experiments

1. Open the Streamlit interface in your browser
2. Configure the number of trials (default: 20)
3. Click "Run Complete Comparative Study" to execute both baseline and PRISM experiments
4. View the privacy-utility trade-off results

## Experimental Design

### Three Scenarios

1. **Baseline (Unmitigated)**: Raw sensitive data flows through all agents
   - Expected: High Exfiltration Rate (ER)
   - Expected: High Task Success Rate (TSR)

2. **PRISM Framework**: Semantic minimization with restricted information
   - Expected: Low Exfiltration Rate (ER ≈ 0)
   - Expected: Preserved Task Success Rate (TSR)

### Medical Use Case

The experiment simulates a multi-agent medical workflow:

- **Sensitive Data**: Medical condition + Treatment ID + Patient ID
- **Agent A**: Diagnosis/Input Encoding (with SM in PRISM mode)
- **Agent B**: Treatment Recommendation
- **Agent C**: Pricing and Final Output

### Metrics

- **Exfiltration Rate (ER)**: Percentage of trials where adversary successfully reconstructs secrets
- **Task Success Rate (TSR)**: Percentage of trials with successful task completion
- **Privacy-Utility Score**: Combined metric favoring low ER and high TSR

## Key Components

### Semantic Minimization (SM)
```python
# Transforms sensitive input
"I have Diabetic Ketoacidosis (DKA) and my ID is 12345"
# Into privacy-preserving equivalent
"I have Chronic Ailment Category and my ID is PID_Hashed"
```

### Restricted Information (RI)
```python
# Access Control List
AGENT_ACL = {
    "Agent_A": ["full_secret_s", "messages"],      # Can see original
    "Agent_B": ["sanitized_uom", "messages"],      # Only sanitized
    "Agent_C": ["sanitized_uom", "messages"],      # Only sanitized
}
```

### Adversarial Probing
The system includes an adversarial LLM that attempts to reconstruct secrets from the cumulative message logs, simulating privacy attacks.

## Expected Results

- **Privacy Improvement**: ~70-90% reduction in Exfiltration Rate
- **Utility Preservation**: ~90-100% Task Success Rate maintained
- **PZPP Mitigation**: Demonstrated through message log analysis

## Testing

Run individual tests:

```python
python metrics.py  # Test adversarial probing and TSR evaluation
```

## Architecture Details

### LangGraph Workflow
```
User Input → Agent A (SM) → Agent B (Treatment) → Agent C (Pricing) → Final Output
                ↓              ↓                    ↓
            Message Log  → Message Log  →   Message Log
                              ↓
                      Adversarial Probe
```

### State Scrubbing
In PRISM mode, Agent A actively removes sensitive information from the shared state before it reaches subsequent agents or the cumulative log.

## Limitations

- Uses free-tier OpenAI API (gpt-3.5-turbo)
- Focused on medical use case (extensible to other domains)
- Proof-of-concept implementation (not production-ready)

## Academic Context

This implementation serves as empirical validation for masters thesis research on privacy-preserving multi-agent LLM systems. The PRISM framework addresses the fundamental privacy-utility trade-off in agentic AI workflows.

## Contributing

This is a research prototype. For questions or collaborations on privacy-preserving AI systems, please refer to the thesis documentation.

## License

Academic research use. Please cite appropriately if using this work.