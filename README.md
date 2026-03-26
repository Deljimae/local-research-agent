## 🚀 Getting Started

### Prerequisites
- [uv](https://docs.astral.sh) installed (Fast Python package manager).
- API keys for your selected LLM provider, Exa, and OpenWeather.

### Installation
1. **Clone the repository**:
   ```bash
   git clone <https://github.com/Deljimae/agent>
   cd AGENTS
   ```

2. **env variables**:

   ```env
   # LLM Provider selection
   LLM_PROVIDER=openai
   LLM_MODEL=gpt-4o-mini

   # Provider keys
   OPENAI_API_KEY=your_openai_key_here
   ANTHROPIC_API_KEY=your_anthropic_key_here

   # Tools
   EXA_API_KEY=your_exa_key_here
   OPENWEATHER_API_KEY=your_openweather_key_here
   ```

   Anthropic example:
   ```env
   LLM_PROVIDER=anthropic
   LLM_MODEL=claude-3-5-sonnet-latest
   ```

3. **Run the Agent**
   ```bash
   uv run main.py
   ```

## 🎯 Example Queries to Try

Once the agent is running, try these "stress tests" to see the MCP and Memory systems in action:

1. **The Directory Check (MCP Discovery)**:
   > "List the files in my project to make sure you can see them."
   *Tests: `inspect_project` tool and local server connectivity.*

2. **The Self-Awareness Test (Local Intelligence)**:
   > "Read the code in agent/mcp_client.py and explain how you connect to the local server."
   *Tests: `read_code_file` and the agent's ability to analyze its own architecture.*

3. **The Multi-Tool Research (Full Orchestration)**:
   > "Search Exa for the latest news on MCP servers, then save a summary of what you find to a new file called mcp_research.md."
   *Tests: Cloud Search (Exa) + Reasoning + Local Write (MCP `write_research_log`) in one autonomous loop.*
