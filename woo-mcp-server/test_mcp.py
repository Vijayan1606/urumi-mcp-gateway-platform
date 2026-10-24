import asyncio
import httpx

URL = "http://127.0.0.1:8000/mcp"

HEADERS = {
    "Accept": "application/json, text/event-stream",
    "Content-Type": "application/json",
}


async def main():
    async with httpx.AsyncClient(timeout=30) as client:

        # Step 1: Initialize the MCP session
        response = await client.post(
            URL,
            headers=HEADERS,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "urumi-test-client",
                        "version": "1.0.0",
                    },
                },
            },
        )

        response.raise_for_status()

        session_id = response.headers.get("mcp-session-id")

        if not session_id:
            print("Failed to create MCP session.")
            print(response.text)
            return

        print("MCP session initialized successfully.")

        # Step 2: Prepare session headers
        headers = {
            **HEADERS,
            "Mcp-Session-Id": session_id,
        }

        # Step 3: Complete MCP initialization
        response = await client.post(
            URL,
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
            },
        )

        if response.status_code not in (200, 202):
            print("MCP initialization notification failed.")
            print("HTTP status:", response.status_code)
            print(response.text)
            return

        # Step 4: Update WooCommerce order status through MCP
        response = await client.post(
            URL,
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "update_order_status",
                    "arguments": {
                        "order_id": 15,
                        "status": "completed",
                    },
                },
            },
        )

        print("\nTool-call HTTP status:", response.status_code)
        print("MCP response:")
        print(response.text)

        response.raise_for_status()

        if '"isError":false' in response.text or '"isError": false' in response.text:
            print("\nSUCCESS: update_order_status executed without an MCP tool error.")
        else:
            print(
                "\nCheck the response above to determine whether "
                "the tool succeeded or returned an MCP error."
            )


if __name__ == "__main__":
    asyncio.run(main())
