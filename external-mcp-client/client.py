import asyncio
import os
import getpass

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


GATEWAY_URL = "http://127.0.0.1:8004/mcp/"


async def main():
    api_key = getpass.getpass("Enter your Urumi API key: ").strip()

    if not api_key:
        print("Error: API key cannot be empty.")
        return

    headers = {
        "Authorization": f"Bearer {api_key}",
    }

    try:
        async with streamablehttp_client(
            GATEWAY_URL,
            headers=headers,
            timeout=30,
            sse_read_timeout=60,
        ) as (read_stream, write_stream, _):
            async with ClientSession(
                read_stream,
                write_stream,
            ) as session:
                # Initialize the MCP connection.
                await session.initialize()

                print("\nConnected to Urumi MCP Gateway.")

                # Discover available tools.
                result = await session.list_tools()

                print(f"\nDiscovered {len(result.tools)} tools:\n")

                for tool in result.tools:
                    print(f"- {tool.name}: {tool.description or 'No description'}")

                # Optional tool execution.
                tool_name = input(
                    "\nEnter a tool name to execute, "
                    "or press Enter to exit: "
                ).strip()

                if not tool_name:
                    return

                matching_tools = [
                    tool for tool in result.tools
                    if tool.name == tool_name
                ]

                if not matching_tools:
                    print("Tool not found. Check the exact name above.")
                    return

                arguments = {}

                if tool_name.endswith("list_products"):
                    page = input("Page number (default 1): ").strip()
                    per_page = input("Products per page (default 5): ").strip()

                    arguments = {
                        "page": int(page) if page else 1,
                        "per_page": int(per_page) if per_page else 5,
                    }

                elif tool_name.endswith("list_orders"):
                    per_page = input("Orders per page (default 5): ").strip()
                    after = input("After date (optional, ISO format): ").strip()
                    before = input("Before date (optional, ISO format): ").strip()

                    arguments = {
                        "per_page": int(per_page) if per_page else 5
                    }
                    if after:
                        arguments["after"] = after
                    if before:
                        arguments["before"] = before

                confirmation = input(
                    f"Execute {tool_name}? (yes/no): "
                ).strip().lower()

                if confirmation != "yes":
                    print("Execution cancelled.")
                    return

                result = await session.call_tool(
                    tool_name,
                    arguments=arguments,
                )

                print("\nTool result:")

                for content in result.content:
                    if hasattr(content, "text"):
                        print(content.text)
                    else:
                        print(content)

                if result.isError:
                    print("\nThe MCP tool reported an error.")

    except Exception as exc:
        print(f"\nMCP connection or request failed: {type(exc).__name__}")
        print("Check that the gateway is running and the API key is valid.")


if __name__ == "__main__":
    asyncio.run(main())
