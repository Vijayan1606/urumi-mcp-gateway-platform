import asyncio
import os
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def main():
    key = os.environ.get("URUMI_GATEWAY_API_KEY")
    if not key:
        raise RuntimeError("Set URUMI_GATEWAY_API_KEY before running.")

    headers = {"Authorization": f"Bearer {key}"}

    async with streamablehttp_client(
        "http://127.0.0.1:8004/mcp",
        headers=headers,
    ) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.list_tools()

            print("Tools exposed through the live MCP endpoint:")
            for tool in result.tools:
                print(f"- {tool.name}")

            matches = [
                tool for tool in result.tools
                if "create_order" in tool.name
            ]
            print(f"\ncreate_order matches: {len(matches)}")

asyncio.run(main())
