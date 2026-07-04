"""Standalone MCP demonstration — no AI application required.

Connects to the ScamShield MCP server in-process, lists the available tools,
and runs check_message on the text you pass (or a sample scam text).

    python mcp_server/demo_client.py "URGENT: buy gift cards now!"
"""
from __future__ import annotations

import asyncio
import json
import sys

from fastmcp import Client

from server import mcp

SAMPLE = ("URGENT: Your bank account has been locked. Verify your PIN at "
          "secure-verify-account.tk within 24 hours or it will be closed!")


async def main() -> None:
    text = " ".join(sys.argv[1:]).strip() or SAMPLE

    async with Client(mcp) as client:
        tools = await client.list_tools()
        print("Tools exposed over MCP:")
        for tool in tools:
            print(f"  - {tool.name}: {(tool.description or '').splitlines()[0]}")

        print(f'\nCalling check_message("{text[:70]}{"…" if len(text) > 70 else ""}")\n')
        result = await client.call_tool("check_message", {"text": text})
        data = result.data

        print(f"Risk level : {data['risk_level'].upper()} "
              f"(score {data['risk_score']})")
        print(f"Summary    : {data['summary']}")
        print(f"Next step  : {data['recommended_action']}")
        if data.get("flags"):
            print("Red flags  :")
            for flag in data["flags"]:
                print(f"  - {flag['title']} (evidence: {', '.join(flag['evidence'][:2])})")


if __name__ == "__main__":
    asyncio.run(main())
