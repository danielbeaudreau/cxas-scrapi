---
name: cxas-insights-miner
description: >-
  Mines online conversations from Contact Center Insights and runtime errors from Cloud Logging
  to generate new SimulationEvals test cases. Use when creating simulation evaluations from real user
  interactions or when debugging runtime failures that are only visible in Cloud Logging.
---

# CXAS Insights Miner

This skill provides tools to fetch online conversations from Contact Center Insights and correlate them with runtime errors from Cloud Logging. It then converts these interactions into robust test cases for the SCRAPI `SimulationEvals` framework.

---

## Execution Rules & Constraints

> [!IMPORTANT]
> 1. **Resource Name Verification**: Always ask the user for the target GCP Project ID, Location, and App Name before running any fetch operations.
> 2. **Output Directory**: Ask the user for a base output directory to store the fetched conversations, logs, and generated test cases.
> 3. **Log Verification**: After running any script, verify its success by reading the output files before proceeding to the next step.

---

## Workflows

### 1. Fetch Online Conversations
Fetch conversations from Contact Center Insights for a specific project and location.

**Command:**
```bash
python .agents/skills/cxas-insights-miner/scripts/fetch_conversations.py \
  --project "MY_PROJECT" \
  --location "us-central1" \
  --output-dir "/path/to/output" \
  --limit 20
```

### 2. Fetch Cloud Logging Errors
Fetch runtime errors from Cloud Logging that occurred in the target environment.

**Command:**
```bash
python .agents/skills/cxas-insights-miner/scripts/fetch_cloud_logs.py \
  --project "MY_PROJECT" \
  --output-dir "/path/to/output" \
  --limit 50
```

### 3. Convert Insights to SimulationEvals
Convert the fetched conversations and correlated errors into simulation test cases using Gemini.

**Command:**
```bash
python .agents/skills/cxas-insights-miner/scripts/convert_insights.py \
  --output-dir "/path/to/output" \
  --project "MY_PROJECT" \
  --location "us-central1"
```
