import os
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("tangerine")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")


async def make_request(
    url: str, method: str = "GET", data: dict[str, Any] = None
) -> dict[str, Any] | None:
    token = (
        os.environ["TANGERINE_TOKEN"]
        if MCP_TRANSPORT == "stdio"
        else mcp.get_context().request_context.request.headers["X-Tangerine-Token"]
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    async with httpx.AsyncClient() as client:
        if method.upper() == "GET":
            response = await client.request(method, url, headers=headers, params=data)
        else:
            response = await client.request(method, url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()


async def search(assistant_name: str, search_text: str) -> str:
    base_url = os.environ["TANGERINE_URL"]
    assistants_url = f"{base_url}/api/assistants"
    assistants = await make_request(assistants_url)
    assistant_id = next(
        (
            assistant["id"]
            for assistant in assistants["data"]
            if assistant["name"] == assistant_name
        ),
        None,
    )
    if assistant_id is None:
        raise ValueError(f"Assistant with name {assistant_name} not found")

    search_url = f"{base_url}/api/assistants/{assistant_id}/search"
    return await make_request(search_url, "POST", data={"query": search_text})


@mcp.tool()
async def search_managed_openshift(search_text: str) -> str:
    """Perform search to find information about Managed OpenShift."""
    return await search("managed-openshift", search_text)


@mcp.tool()
async def search_app_interface(search_text: str) -> str:
    """Perform search to find information about App Interface."""
    return await search("app-sre-app-interface", search_text)


@mcp.tool()
async def search_konflux(search_text: str) -> str:
    """Perform search to find information about Konflux."""
    return await search("konflux", search_text)


if __name__ == "__main__":
    mcp.run(transport=MCP_TRANSPORT)
