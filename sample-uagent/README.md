# Sample uAgent with ASI-Telemetry & Self-Healing Testing

This repository contains a standalone [Fetch.ai uAgent](https://fetch.ai/) configured with the official **`asi-telemetry` SDK** and an **intentional runtime defect** to test the **ASI:One in-chat debugging and self-healing loop**.

---

## 🚀 Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```
Or directly install the official telemetry SDK:
```bash
pip install asi-telemetry uagents
```

### 2. Environment Configuration (`.env`)
The environment is pre-configured with your active ASI-Telemetry API key:
```env
ASI_API_KEY=asi_live_39324b2ba7eba4cb598746e38d5547cc
TELEMETRY_BACKEND_URL=http://localhost:8080
AGENT_PORT=8300
AGENT_NAME=sample_demo_agent
```

---

## 🧪 Testing the Agent & Triggering the Defect

### Option A: Quick Local Test (Single Command)
Run the automated runner to test both healthy execution and defect capture:
```bash
python run_local_test.py
```
**Output:**
1. Executes `format_agent_status` successfully $\to$ Dispatches healthy telemetry to ClickHouse.
2. Executes `compute_analytics` with missing `completion_tokens` $\to$ Triggers `KeyError: 'completion_tokens'` and records the defect in telemetry.

### Option B: Running Full uAgent Network
1. In Terminal 1, run the main agent:
   ```bash
   python agent.py
   ```
2. In Terminal 2, run the companion test client:
   ```bash
   python test_client.py
   ```

### Option C: Seed Realistic Dummy Telemetry
To populate your dashboard and ASI:One with realistic telemetry data (metrics, LLM traces, multi-model execution, and error traces) directly:
```bash
# Seed all dummy metrics & LLM traces from dummy_data.json
python seed_dummy_data.py

# Or simulate live real-time telemetry streaming every 2s
python seed_dummy_data.py --stream --interval 2.0
```
- **Data File**: [`dummy_data.json`](dummy_data.json) contains preconfigured agent queries, tool metrics, and LLM traces.
- **Direct Error Injection**: [`inject_dummy_error.py`](inject_dummy_error.py) for testing ASI:One defect diagnosis.

---

## 🛠️ Fixing the Defect Live via ASI:One

Once the error triggers, you can debug and self-heal the repository directly from **ASI:One**:

### 1. Diagnose in ASI:One
Send this in your ASI:One chat with the telemetry agent:
```text
diagnose
```
**ASI:One Response:**
> 🔍 **Runtime Diagnostic Report:**
> - **Error Category:** `agent_defect`
> - **Sanitized Error:** `KeyError: 'completion_tokens'`
> - **File:** `tools.py`
>
> 🛠️ **Proposed Patch (`tools.py`):**
> ```diff
> - completion_tokens = payload["completion_tokens"]
> + completion_tokens = payload.get("completion_tokens", 0)
> ```

### 2. Select Your Repository
Tell the agent which GitHub repository to patch:
```text
select repo <your-github-username>/<your-repo-name>
```

### 3. Approve and Push PR via GitHub MCP
Authorize the automated fix:
```text
approve pr
```
**ASI:One Response:**
> 🚀 **Pull Request Created Successfully!**
> - **Branch:** `fix/err_...`
> - **Pull Request:** `https://github.com/<your-username>/<your-repo>/pull/1`
