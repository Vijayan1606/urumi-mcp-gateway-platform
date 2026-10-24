import asyncio
import traceback
from app.mcp_client import MCPUpstreamClient


async def main():
    client = MCPUpstreamClient("http://localhost:8001/mcp")

    try:
        await client.connect()
        print("Connected successfully")

        tools = await client.list_tools()
        print(f"Discovered {len(tools)} tools")

        for tool in tools:
            print("-", tool["name"])

    except BaseException:
        traceback.print_exc()

    finally:
        try:
            await client.close()
            print("Client closed")
        except BaseException:
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
