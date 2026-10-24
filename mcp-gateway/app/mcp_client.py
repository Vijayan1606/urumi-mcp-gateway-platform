from contextlib import AsyncExitStack

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


class MCPUpstreamClient:
    def __init__(self, url: str, headers: dict[str, str] | None = None):
        self.url = url
        self.headers = headers or {}
        self.exit_stack = AsyncExitStack()
        self.session = None
        self.connected = False

    async def connect(self):
        """Open an authenticated MCP connection and initialize its session."""

        if self.connected:
            return self

        try:
            read_stream, write_stream, _ = (
                await self.exit_stack.enter_async_context(
                    streamablehttp_client(
                        self.url,
                        headers=self.headers,
                    )
                )
            )

            self.session = await self.exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )

            await self.session.initialize()
            self.connected = True

            return self

        except BaseException:
            await self.exit_stack.aclose()
            raise

    async def list_tools(self):
        """Retrieve tools exposed by the upstream MCP server."""

        if not self.connected or self.session is None:
            raise RuntimeError("MCP client is not connected")

        result = await self.session.list_tools()

        return [
            {
                "name": tool.name,
                "description": tool.description or "",
                "inputSchema": tool.inputSchema,
            }
            for tool in result.tools
        ]

    async def call_tool(self, name: str, arguments: dict):
        """Execute a tool on the upstream MCP server."""

        if not self.connected or self.session is None:
            raise RuntimeError("MCP client is not connected")

        return await self.session.call_tool(name, arguments)

    async def close(self):
        """Close the session and transport resources."""

        if self.exit_stack is not None:
            await self.exit_stack.aclose()

        self.session = None
        self.connected = False


async def main():
    import asyncio

    client = MCPUpstreamClient("http://localhost:8001/mcp")

    try:
        await client.connect()
        print("Connected to WooCommerce MCP server!")

        tools = await client.list_tools()

        print("\nAvailable tools:")
        for tool in tools:
            print(f"- {tool['name']}: {tool['description']}")

    except Exception as error:
        print(f"Connection test failed: {type(error).__name__}: {error}")
        raise

    finally:
        await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
