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
            result = await session.list_tools()

            names = sorted(tool.name for tool in result.tools)
            print(f"Discovered {len(names)} tools:")
            for name in names:
                print(name)

            expected = [
                "woocommerce__list_products",
                "inventory__list_inventory",
                "customer_support__search_faq",
                "gateway_status",
            ]

            missing = [name for name in expected if name not in names]
            if missing:
                print("MISSING:", ", ".join(missing))
            else:
                print("PASS: All expected namespaced tools are exposed.")

asyncio.run(main())
