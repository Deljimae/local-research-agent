# AGENTS

A small command-line research agent with provider adapters, local tools, MCP-based project inspection, lightweight skill selection, and an experimental memory layer.

This is a local research/demo project, not a production assistant.

## What Is Included

- OpenAI and Anthropic chat provider adapters
- Built-in tools for Exa search and OpenWeather lookup
- A local FastMCP server with project inspection and note-writing tools
- Markdown-based skills loaded from `skills/`
- SQLite-backed memory experiments using OpenAI embeddings

## Setup

Requirements:

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- API keys for the provider/tools you plan to use

```bash
git clone https://github.com/Deljimae/local-research-agent
cd local-research-agent
uv sync
cp .env.example .env
```

Fill in `.env`. OpenAI is currently required for embeddings even when `LLM_PROVIDER=anthropic`.

```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
EXA_API_KEY=your_exa_key_here
OPENWEATHER_API_KEY=your_openweather_key_here
```

## Run

```bash
uv run main.py
```

Type `exit` or `quit` to end the session.

## Structure

```text
main.py              # CLI loop
config.py            # environment config and SDK clients
agent/               # agent loop, providers, memory, skills, MCP client
tools/               # static tool registry and implementations
skills/              # local skill instructions
mcp_server/          # local FastMCP server
```

## Example Prompts

```text
List the files in my project to make sure you can see them.
```

```text
Read agent/mcp_client.py and explain how it connects to the local server.
```

```text
Use the code-review skill to review agent/core.py.
```

## Limitations

- Tool calls run sequentially.
- Memory retrieval is simple and local.
- The MCP server exposes only a few project-focused tools.
- Live behavior depends on valid OpenAI/Anthropic, Exa, and OpenWeather credentials.
- There is no formal test suite yet.

Offline syntax check:

```bash
python -m compileall agent tools main.py config.py mcp_server/server.py mcp_server/main.py
```
