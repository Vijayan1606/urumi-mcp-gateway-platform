import json
import httpx

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

MCP_URL = "http://localhost:8001/mcp"

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}


# ---------------------------------------------------------
# RESPONSE PARSER
# ---------------------------------------------------------

def parse_response(response):
    """Parse JSON or Server-Sent Events MCP responses."""

    text = response.text

    for line in text.splitlines():
        if line.startswith("data: "):
            try:
                return json.loads(line[6:])
            except json.JSONDecodeError:
                continue

    try:
        return response.json()
    except json.JSONDecodeError:
        return {"raw_response": text}


# ---------------------------------------------------------
# MCP TOOL CALL
# ---------------------------------------------------------

def call_tool(client, name, arguments, request_id):
    """Call an MCP tool and display a concise result."""

    response = client.post(
        MCP_URL,
        headers=HEADERS,
        json={
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments,
            },
        },
    )

    print(f"\n{'=' * 55}")
    print(f"TOOL: {name}")
    print(f"{'=' * 55}")
    print("HTTP status:", response.status_code)

    response.raise_for_status()

    result = parse_response(response)

    if result.get("error"):
        print("JSON-RPC error:", result["error"])
        return result

    tool_result = result.get("result", result)

    if tool_result.get("isError"):
        print("Tool execution failed.")

    # MCP tool results commonly contain JSON in text blocks.
    for item in tool_result.get("content", []):
        if item.get("type") == "text":
            text = item["text"]

            try:
                parsed = json.loads(text)
                print(json.dumps(parsed, indent=2)[:3000])
            except json.JSONDecodeError:
                print(text[:3000])

    return result


# ---------------------------------------------------------
# MAIN TEST
# ---------------------------------------------------------

def main():

    with httpx.Client(timeout=30) as client:

        # 1. Initialize MCP
        print("\n1. INITIALIZING MCP")

        response = client.post(
            MCP_URL,
            headers=HEADERS,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "kubernetes-mcp-test",
                        "version": "1.0.0",
                    },
                },
            },
        )

        print("Initialize HTTP status:", response.status_code)
        response.raise_for_status()

        # Keep the MCP session ID if the server provides one.
        session_id = response.headers.get("Mcp-Session-Id")

        if session_id:
            HEADERS["Mcp-Session-Id"] = session_id

        # 2. Complete initialization
        print("\n2. COMPLETING INITIALIZATION")

        response = client.post(
            MCP_URL,
            headers=HEADERS,
            json={
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
            },
        )

        print("Notification HTTP status:", response.status_code)
        response.raise_for_status()

        # 3. Discover available tools
        print("\n3. DISCOVERING MCP TOOLS")

        response = client.post(
            MCP_URL,
            headers=HEADERS,
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {},
            },
        )

        response.raise_for_status()

        tool_response = parse_response(response)
        tools = tool_response.get("result", {}).get("tools", [])

        print("Available tools:")

        for tool in tools:
            print(f"  - {tool['name']}: {tool.get('description', '')}")

        expected_tools = {
            "list_products",
            "create_product",
            "list_orders",
            "get_order",
            "update_order_status",
        }

        actual_tools = {tool["name"] for tool in tools}

        if expected_tools.issubset(actual_tools):
            print("\nPASS: All five expected tools are registered.")
        else:
            missing = expected_tools - actual_tools
            print("\nFAIL: Missing tools:", sorted(missing))
            return

        # 4. Test listing products
        call_tool(
            client,
            "list_products",
            {
                "page": 1,
                "per_page": 5,
            },
            3,
        )

        # 5. Test listing orders
        call_tool(
            client,
            "list_orders",
            {
                "page": 1,
                "per_page": 5,
            },
            4,
        )

        # 6. Test retrieving an existing order
        call_tool(
            client,
            "get_order",
            {
                "order_id": 15,
            },
            5,
        )

        # 7. Test product creation
        # This creates one real product in your WooCommerce store.
        call_tool(
            client,
            "create_product",
            {
                "name": "Urumi MCP Verification Product",
                "regular_price": "199",
                "description": (
                    "Created to verify MCP product creation."
                ),
                "short_description": (
                    "MCP verification product."
                ),
                "stock_quantity": 2,
            },
            6,
        )

        # 8. Do not modify an existing order during this test.
        print("\nSkipping update_order_status.")
        print("Existing orders have not been modified by this test.")

        print("\n" + "=" * 55)
        print("MCP TEST RUN COMPLETED")
        print("=" * 55)


if __name__ == "__main__":
    try:
        main()
    except httpx.HTTPError as error:
        print("\nHTTP ERROR:", error)
    except Exception as error:
        print(f"\nERROR: {type(error).__name__}: {error}")
