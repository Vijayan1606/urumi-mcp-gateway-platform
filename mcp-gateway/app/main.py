from fastapi import FastAPI

app = FastAPI(
    title="Urumi MCP Gateway",
    description="A centralized gateway for multiple MCP servers",
    version="1.0.0",
)


@app.get("/")
async def root():
    return {
        "message": "Welcome to Urumi MCP Gateway",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "urumi-mcp-gateway",
    }
