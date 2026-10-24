from contextlib import asynccontextmanager
from datetime import datetime, timezone
from itertools import count

import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route


# Initialize the Customer Support MCP server
mcp = FastMCP(
    "Urumi Customer Support MCP",
    host="0.0.0.0",
    port=8000,
    streamable_http_path="/",
    stateless_http=True,
    json_response=True,
)


# Sample FAQ data
FAQS = [
    {
        "question": "How can I track my order?",
        "answer": (
            "You can track your order using the tracking link "
            "provided in your order confirmation email."
        ),
        "category": "orders",
    },
    {
        "question": "What payment methods are accepted?",
        "answer": (
            "Available payment methods depend on the checkout options "
            "enabled by the store."
        ),
        "category": "payments",
    },
    {
        "question": "Can I cancel my order?",
        "answer": (
            "Contact customer support as soon as possible. "
            "Cancellation depends on the order's fulfillment status."
        ),
        "category": "orders",
    },
    {
        "question": "How do I return a product?",
        "answer": (
            "Contact customer support with your order number and "
            "the reason for the return."
        ),
        "category": "returns",
    },
]


# Sample shipping policy
SHIPPING_POLICY = {
    "standard_shipping": {
        "estimated_delivery": "3-5 business days",
        "description": "Standard delivery for eligible domestic orders.",
    },
    "express_shipping": {
        "estimated_delivery": "1-2 business days",
        "description": "Faster delivery where the service is available.",
    },
    "processing_time": "Orders are generally processed within 1-2 business days.",
    "tracking": (
        "Tracking information is provided when an order has been dispatched."
    ),
    "note": (
        "These are demonstration policies. Actual shipping terms depend "
        "on the store's configured policies."
    ),
}


# In-memory support tickets for this demonstration
tickets = []
ticket_counter = count(1001)


@mcp.tool()
def search_faq(query: str, category: str = "") -> dict:
    """Search customer support FAQs by keyword and optional category."""

    query_terms = query.lower().split()
    category_filter = category.strip().lower()

    results = []

    for faq in FAQS:
        searchable_text = (
            faq["question"] + " " + faq["answer"] + " " + faq["category"]
        ).lower()

        matches_query = (
            not query_terms
            or any(term in searchable_text for term in query_terms)
        )

        matches_category = (
            not category_filter
            or faq["category"].lower() == category_filter
        )

        if matches_query and matches_category:
            results.append(faq)

    return {
        "query": query,
        "count": len(results),
        "results": results,
    }


@mcp.tool()
def get_shipping_policy(shipping_type: str = "all") -> dict:
    """Retrieve the store's demonstration shipping policies."""

    shipping_type = shipping_type.strip().lower()

    if shipping_type == "all":
        return SHIPPING_POLICY

    if shipping_type in SHIPPING_POLICY:
        return {
            shipping_type: SHIPPING_POLICY[shipping_type]
        }

    return {
        "error": (
            "Unknown shipping type. Use 'all', 'standard_shipping', "
            "'express_shipping', 'processing_time', or 'tracking'."
        )
    }


@mcp.tool()
def create_support_ticket(
    customer_name: str,
    customer_email: str,
    subject: str,
    description: str,
) -> dict:
    """Create a demonstration customer support ticket."""

    required_fields = {
        "customer_name": customer_name,
        "customer_email": customer_email,
        "subject": subject,
        "description": description,
    }

    for field_name, value in required_fields.items():
        if not value.strip():
            return {
                "success": False,
                "error": f"{field_name} cannot be empty.",
            }

    if "@" not in customer_email:
        return {
            "success": False,
            "error": "Please provide a valid email address.",
        }

    ticket = {
        "ticket_id": next(ticket_counter),
        "customer_name": customer_name.strip(),
        "customer_email": customer_email.strip(),
        "subject": subject.strip(),
        "description": description.strip(),
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    tickets.append(ticket)

    return {
        "success": True,
        "message": "Support ticket created successfully.",
        "ticket": ticket,
    }


@asynccontextmanager
async def lifespan(app):
    async with mcp.session_manager.run():
        yield


async def health(request):
    return JSONResponse({"status": "healthy"})


mcp_app = mcp.streamable_http_app()

app = Starlette(
    routes=[
        Route("/health", health, methods=["GET"]),
        Mount("/", app=mcp_app),
    ],
    lifespan=lifespan,
)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
