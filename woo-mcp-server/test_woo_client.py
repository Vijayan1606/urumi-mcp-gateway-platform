import os
import sys
from woocommerce import API

consumer_key = os.environ.get("WC_CONSUMER_KEY")
consumer_secret = os.environ.get("WC_CONSUMER_SECRET")

if not consumer_key or not consumer_secret:
    print("Credentials are missing.")
    sys.exit(1)

wcapi = API(
    url="http://localhost:8080",
    consumer_key=consumer_key,
    consumer_secret=consumer_secret,
    version="wc/v3",
    timeout=15,
    query_string_auth=True,
)

# Use WordPress's index.php REST route.
wcapi.url = "http://localhost:8080/index.php?rest_route=/wc/v3"

try:
    response = wcapi.get(
        "products",
        params={"per_page": 1},
    )

    print("HTTP status:", response.status_code)

    if response.ok:
        products = response.json()
        print("Authentication successful.")
        print("Products returned:", len(products))

        for product in products:
            print(
                "Product ID:", product.get("id"),
                "| Name:", product.get("name"),
            )
    else:
        print("Response:", response.text[:500])

except Exception as exc:
    print("Request failed:", type(exc).__name__)
