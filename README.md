# PRISM Privacy Framework - Thesis Validation

## Overview

This project implements the **PRISM (Privacy through Restricted Information & Semantic Minimization) Framework** to address the **Puzzle Piece Privacy Problem (PZPP)** in multi-agent LLM systems. This is an empirical validation system for masters thesis research on privacy-preserving AI.

### Core Problem: Puzzle Piece Privacy Problem (PZPP)
Individual agent outputs may seem non-sensitive, but when combined across multiple agents, they can reveal sensitive information through cumulative leakage in reflection logs.

### Solution: PRISM Framework
- **Restricted Information (RI)**: Enforces access control through LangGraph state management
- **Semantic Minimization (SM)**: Transforms sensitive inputs into privacy-preserving "Units of Meaningfulness"

## Project Structure

```
prism_experiment/
├── main.py              # Streamlit interface with comprehensive metrics
├── agents.py            # LangGraph multi-agent workflow with structured output
├── metrics.py           # ER/TSR calculation with enhanced error handling
├── config.py            # Configuration and data templates
├── prism_logic.py       # Core PRISM mechanism (RI + SM)
├── requirements.txt     # Production dependencies
├── .env                 # API keys configuration
├── test_system.py       # Comprehensive validation tests
└── README.md           # This file
```

## Quick Start

### 1. Setup Environment

```bash
# Create and activate virtual environment
python -m venv prism_env
# Windows:
.\prism_env\Scripts\Activate.ps1
# Mac/Linux:
source prism_env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Key

Create a `.env` file with your OpenAI API key:

```env
# OpenAI Configuration (Required)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
LLM_PROVIDER=openai
TEMPERATURE=0.1
```

#### Getting API Keys:
- **OpenAI**: Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)
- The system uses **gpt-4o-mini** for budget-optimized research validation

### 3. Validate Setup

Before running experiments, validate your configuration:

```bash
python test_system.py
```

Expected output: `ALL TESTS PASSED! 🎉`

### 4. Run Experiments

```bash
streamlit run main.py
```

Open your browser to `http://localhost:8501` to access the experimental interface.

### Streamlit Interface

The experimental interface provides real-time adversarial testing and comprehensive privacy-utility analysis:

![PRISM Streamlit Interface](streamlit%20interface%20image.png)

**Key Features:**
- **Interactive Experiment Configuration**: Set trial counts and scenarios
- **Real-time Privacy-Utility Metrics**: Live ER/TSR calculation during experiments
- **Adversarial Testing Panel**: Custom attack scenarios and reconstruction attempts
- **Comparative Analysis**: Side-by-side BASELINE vs PRISM performance visualization
- **Detailed Results Display**: Example logs showing successful/failed privacy protection

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

## Core Framework Components

### 1. Multi-Agent Workflow (agents.py)
- **Agent A**: Diagnosis agent with semantic minimization capability
- **Agent B**: Treatment recommendation agent  
- **Agent C**: Pricing and final output agent
- **LangGraph Integration**: Structured state management with reflection log tracking

### 2. PRISM Mechanism (prism_logic.py)

#### Semantic Minimization (SM)
Transforms sensitive inputs while preserving utility:
```
Original: "I have Diabetic Ketoacidosis (DKA) and my ID is ID_12345"
SM Output: "I have a Metabolic Disorder and my ID is PID_Anonymous" 
```

#### Restricted Information (RI)
Enforces access control per agent:
- Agent A: Full input access for initial processing
- Agent B: Sanitized input only
- Agent C: Treatment context only

### 3. Privacy-Utility Metrics (metrics.py)

#### Key Metrics
- **Exfiltration Rate (ER)**: Adversary's success rate in reconstructing secrets from reflection logs
- **Task Success Rate (TSR)**: System's ability to complete the medical workflow correctly
- **RSL (Reflective Steps to Leakage)**: Complexity measure for adversarial reconstruction
- **Semantic Fidelity**: Preservation of semantic meaning after minimization

#### Expected Results
- **BASELINE**: High ER (~70-90%), High TSR (~95%) - demonstrates PZPP vulnerability
- **PRISM**: Low ER (~0-20%), High TSR (~90-95%) - demonstrates solution effectiveness

## Sample Medical Scenarios

The framework uses realistic medical test cases:
- **Conditions**: Diabetic Ketoacidosis, Chronic Heart Failure, Acute Bronchitis
- **Treatments**: RX_Alpha_7, Treatment_Beta_12, Medication_Gamma_3
- **Patient IDs**: ID_12345, ID_98765, ID_54321

## Research Validation

### For Thesis Research
This implementation provides empirical evidence for:
- Privacy leakage in multi-agent systems (BASELINE results)
- Effectiveness of PRISM framework (comparative improvement)
- Privacy-utility trade-off optimization

### Statistical Significance
- N=100+ trials for robust statistical analysis
- Structured output ensures reliable TSR detection
- Comprehensive adversarial testing framework
- Reproducible experimental design

## Technical Architecture

### Key Dependencies
- **LangChain/LangGraph**: Multi-agent orchestration
- **OpenAI GPT-4o-mini**: Budget-optimized LLM inference
- **Streamlit**: Interactive research interface
- **Pydantic**: Structured output validation for reliable TSR measurement

### Error Handling
- API failure boundaries with retry logic
- Invalid response detection and recovery
- Graceful degradation for research continuity

## Testing Your Setup

Before running experiments:

```bash
python test_system.py
```

Expected output: `ALL TESTS PASSED! 🎉`

This validates:
- API connectivity
- Semantic minimization functionality
- Adversarial probing system
- Graph execution workflow

## Academic Context

This implementation serves as empirical validation for doctoral thesis research on privacy-preserving multi-agent LLM systems. The PRISM framework addresses the fundamental **Puzzle Piece Privacy Problem (PZPP)** where individual agent outputs appear safe but collectively leak sensitive information through reflection logs.

### Key Research Contributions
- Semantic Minimization approach preserving utility
- Multi-agent access control through LangGraph state management
- Empirical demonstration of privacy-utility trade-off optimization
- Adversarial validation framework for privacy claims

## License

Academic research use. Please cite appropriately if using this work for research purposes.