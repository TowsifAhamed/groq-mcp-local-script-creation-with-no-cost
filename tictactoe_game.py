import os
import anyio
from mcp.client.session_group import ClientSessionGroup, SseServerParameters


async def main() -> None:
    """Ask the MCP server to build and run a snake game."""
    url = os.getenv("MCP_URL", "http://localhost:4876/sse")
    model = os.getenv("MCP_MODEL", "meta-llama/llama-4-maverick-17b-128e-instruct")
    prompt = (
        "Create a simple tictactoe game that runs automatically. "
        "Use the `write_file` tool to save it as `tictactoe.py` in the game_lab "
        "directory (the directory is already there). Then execute it with the `run_cmd` tool so the game "
        "plays automatically for both sides as a simulation."
    )
    messages = [{"role": "user", "content": prompt}]
    async with ClientSessionGroup() as group:
        session = await group.connect_to_server(SseServerParameters(url=url))
        result = await session.call_tool(
            "compound_tool",
            {"messages": messages, "model": model},
        )
        text_blocks = [b.text for b in result.content if hasattr(b, "text")]
        if text_blocks:
            print("".join(text_blocks))


if __name__ == "__main__":
    anyio.run(main)
