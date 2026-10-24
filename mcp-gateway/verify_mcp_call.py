import asyncio
import os
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def main():
    headers = {
        "Authorization": f"Bearer {os.environ['URUMI_TEST_API_KEY']}"
    }

    async with streamablehttp_client(
        "http://127.0.0.1:8004/mcp",
        headers=headers,
    ) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool(
                "inventory__list_inventory",
                {},
            )

            print("Tool: inventory__list_inventory")
            print(f"Is error: {result.isError}")
            for item in result.content:
                if hasattr(item, "text") and item.text:
                    print(item.text)

            if result.isError:
                raise RuntimeError("MCP tool call returned an error.")

            print("PASS: Namespaced MCP tool call succeeded.")

asyncio.run(main())
