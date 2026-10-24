# Run the complete assignment without paid APIs

The OpenAI Agents SDK is the agent framework. It can use a local model through its OpenAIChatCompletionsModel adapter. You do not need an OpenAI API key or a payment method for this setup.

## Setup

1. Install Ollama from https://ollama.com/download, or use your existing installation.
2. Open the Ollama application. If you use only the CLI, run `ollama serve` in another terminal.
3. Download the model once:

```bash
ollama pull qwen2.5:3b
```

The model is about 1.9 GB. It runs on your device; performance depends on available memory and CPU/GPU speed.

4. From the project folder, prepare Python:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

The provided configuration defaults to:

```dotenv
MODEL_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:3b
OLLAMA_BASE_URL=http://127.0.0.1:11434/v1
```

5. Capture all checks and a real language-model demonstration:

```bash
python scripts/verify.py --live
```

6. Start interactive chat:

```bash
python -m campus_toolkit.agent
```

## What the live check proves

Three natural-language requests are sent to the local language model. The model sees the MCP tool descriptions and selects its calls. The OpenAI Agents SDK executes the calls over stdio through the FastMCP server. The check validates tool-call names, all expected argument values, room constraints, factual summaries and reservation state. Both preference-taking MCP tools require an explicit quiet_only boolean. The host formats displayed answers from validated MCP receipts and never displays the raw model-written final narrative. It does not force tool selection with a hard-coded tool_choice or use the scripted test model.

The application disables OpenAI tracing. In local mode the client connects only to a loopback hostname and uses the placeholder `ollama`, which is not an API key. Optional paid OpenAI mode requires explicitly setting MODEL_PROVIDER=openai and configuring a key; it is not used by default or by the free workflow.

The Free local LLM verification workflow uses a standard Linux runner in this public repository. GitHub documents standard runners as free for public repositories; it does not use a paid API or a larger/GPU runner.

## Sources

- Ollama's official OpenAI-compatible local endpoint: https://docs.ollama.com/api/openai-compatibility
- Official model listing and download size: https://ollama.com/library/qwen2.5:3b
- GitHub Actions billing: https://docs.github.com/en/billing/concepts/product-billing/github-actions

Using a different model is permitted by the technical design while preserving the requested OpenAI Agents SDK. If your instructor separately requires an OpenAI-hosted model, ask whether a local-model demonstration is acceptable; C5 names the SDK and does not explicitly name a required hosted model.
