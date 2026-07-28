import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "agent.settings")
django.setup()

from asgiref.sync import sync_to_async  # noqa: E402
from mcp.server.fastmcp import FastMCP  # noqa: E402

from conversation import memory_tools  # noqa: E402

mcp = FastMCP("agent-memory", host="0.0.0.0", port=8001)

# FastMCP 는 툴을 이벤트 루프 안에서 실행하는데 Django ORM 은 async 컨텍스트에서
# 호출을 거부한다. 툴 본체(memory_tools)는 동기로 두고 sync_to_async 로 감싼다.


@mcp.tool()
async def save_memory(conversation_id: int, key: str, value: str) -> str:
    """Save or update a memory for the conversation.

    Use this when the user shares important personal info, preferences,
    or key facts/decisions worth remembering. Keys are concise English
    snake_case (e.g. "user_name", "preferred_language").
    """
    return await sync_to_async(memory_tools.save_memory)(conversation_id, key, value)


@mcp.tool()
async def list_memory(conversation_id: int) -> list[dict]:
    """List all memories saved for the conversation as key-value pairs."""
    return await sync_to_async(memory_tools.list_memory)(conversation_id)


@mcp.tool()
async def delete_memory(conversation_id: int, key: str) -> str:
    """Delete a saved memory by key for the conversation."""
    return await sync_to_async(memory_tools.delete_memory)(conversation_id, key)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
