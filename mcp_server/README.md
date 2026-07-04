# ScamShield MCP server

Exposes ScamShield's detection engine as [Model Context Protocol](https://modelcontextprotocol.io)
tools. MCP is an open standard, so **any MCP-compatible client** can call the
checkers while it reasons: AI assistants, IDE agents, agent frameworks
(LangChain, CrewAI, OpenAI Agents SDK), workflow tools such as n8n, or plain
Python code. An assistant asked *"is this message my dad got a scam?"* can run
`check_message` itself and answer from the grounded verdict.

## Tools

| Tool | What it does |
|---|---|
| `check_message` | Scam-risk analysis of an SMS/email/transcript |
| `check_url` | Phishing analysis of a web address (lexical + ML + safe live fetch) |
| `check_news` | Style analysis + RAG fact-check of an article or headline |
| `fact_check_claim` | Wikipedia-grounded verdict for one factual claim |
| `check_product` | Fraud assessment of a marketplace listing |

## Quick demo — no AI application required

```bash
python mcp_server/demo_client.py "URGENT: your account is locked, buy gift cards to unlock"
```

This spins up the server in-process over MCP, lists the tools, and runs
`check_message` on your text.

## Connect an MCP client

The server uses stdio transport. Most desktop clients take a JSON entry like
this (adjust paths to your clone; on Windows the interpreter is
`.venv/Scripts/python.exe`):

```json
{
  "mcpServers": {
    "scamshield": {
      "command": "/path/to/scamshield/.venv/bin/python",
      "args": ["/path/to/scamshield/mcp_server/server.py"],
      "env": { "GEMINI_API_KEY": "" }
    }
  }
}
```

CLI-based clients typically register it with a one-liner in the form:

```bash
<client> mcp add scamshield -- /path/to/.venv/bin/python mcp_server/server.py
```

Agent frameworks connect through their MCP adapters (e.g.
`langchain-mcp-adapters` for LangChain/LangGraph, `crewai-tools` for CrewAI)
pointed at the same command.

Everything degrades gracefully without `GEMINI_API_KEY` — verdicts stay
grounded in the ML models and rules; explanations use the built-in templates.
