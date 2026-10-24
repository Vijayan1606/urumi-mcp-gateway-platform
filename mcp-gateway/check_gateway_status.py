import asyncio
import os
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def main():
    api_key = os.environ.get("URUMI_TEST_API_KEY")
    if not api_key:
        print("ERROR: URUMI_TEST_API_KEY is not set in this terminal.")
        return

    headers = {"Authorization": f"Bearer {api_key}"}

    async with streamablehttp_client(
        "http://127.0.0.1:8004/mcp",
        headers=headers
    ) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool("gateway_status", {})

            for item in result.content:
                if hasattr(item, "text") and item.text:
                    print(item.text)

asyncio.run(main())
