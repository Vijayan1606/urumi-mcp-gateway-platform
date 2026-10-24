import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def main():
    url = "http://localhost:8000/"

    async with streamablehttp_client(url) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.list_tools()

            print("\nAvailable Customer Support MCP tools:")
            for tool in result.tools:
                print(f"- {tool.name}: {tool.description}")

            print("\nTesting FAQ search:")
            faq_result = await session.call_tool(
                "search_faq",
                arguments={"query": "track order"},
            )
            print(faq_result)

            print("\nTesting shipping policy:")
            shipping_result = await session.call_tool(
                "get_shipping_policy",
                arguments={"shipping_type": "standard_shipping"},
            )
            print(shipping_result)

            print("\nTesting support ticket creation:")
            ticket_result = await session.call_tool(
                "create_support_ticket",
                arguments={
                    "customer_name": "Test Customer",
                    "customer_email": "test@example.com",
                    "subject": "Order tracking assistance",
                    "description": "I need help tracking my order.",
                },
            )
            print(ticket_result)


if __name__ == "__main__":
    asyncio.run(main())
