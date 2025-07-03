from mcp.server import FastMCP
from pydantic import BaseModel, Field
import subprocess, os, json, textwrap
from groq import AsyncGroq

SANDBOX = os.path.abspath("./game_lab")

# FastMCP application instance used to register tools
app = FastMCP()


class PathArg(BaseModel):
    path: str = Field(..., description="Relative path under ./game_lab/")


@app.tool(name="write_file", description="Create or overwrite a text file")
def write_file(path: PathArg, content: str) -> str:
    full = os.path.join(SANDBOX, path.path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, "w", encoding="utf-8").write(content)
    return f"wrote {path.path}"


@app.tool(name="read_file", description="Read a text file")
def read_file(path: PathArg) -> str:
    full = os.path.join(SANDBOX, path.path)
    return open(full, encoding="utf-8").read()


@app.tool(name="list_files", description="List sandbox dir")
def list_files() -> list[str]:
    out = []
    for root, _, files in os.walk(SANDBOX):
        for f in files:
            out.append(os.path.relpath(os.path.join(root, f), SANDBOX))
    return out


class Cmd(BaseModel):
    cmd: str = Field(..., description="Shell cmd run inside ./game_lab")




from dotenv import load_dotenv
import argparse


def ensure_sandbox() -> None:
    """Create the sandbox directory and git-ignore it if needed."""
    os.makedirs(SANDBOX, exist_ok=True)
    ignore_entry = "game_lab/"
    gitignore = os.path.join(os.getcwd(), ".gitignore")
    lines: list[str] = []
    if os.path.exists(gitignore):
        with open(gitignore, "r", encoding="utf-8") as fh:
            lines = [line.rstrip("\n") for line in fh]
    if ignore_entry not in lines:
        with open(gitignore, "a", encoding="utf-8") as fh:
            if lines and lines[-1] != "":
                fh.write("\n")
            fh.write(f"{ignore_entry}\n")


@app.tool(name="run_cmd", description="Run shell command (e.g. python main.py)")
def run_cmd(arg: Cmd) -> str:
    """Execute a shell command in the sandbox and return its output."""
    try:
        proc = subprocess.run(
            arg.cmd,
            cwd=SANDBOX,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=30,
            check=False,
        )
        output = proc.stdout
    except subprocess.TimeoutExpired as exc:
        output = (exc.stdout or "") + (exc.stderr or "") + "\n<timeout>"
    return output[:4096]


@app.tool(name="compound_tool", description="Agent that uses Groq LLM to call other tools")
async def compound_tool(messages: list[dict], model: str = "mixtral-8x7b-32768") -> list[str]:
    """Use Groq's chat completion API with function calls to invoke tools."""
    client = AsyncGroq()

    tools = [
        {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": "Create or overwrite a text file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["path", "content"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read a text file",
                "parameters": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_files",
                "description": "List sandbox dir",
                "parameters": {"type": "object", "properties": {}},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "run_cmd",
                "description": "Run shell command (e.g. python main.py)",
                "parameters": {
                    "type": "object",
                    "properties": {"cmd": {"type": "string"}},
                    "required": ["cmd"],
                },
            },
        },
    ]

    conversation = messages[:]

    while True:
        response = await client.chat.completions.create(
            model=model,
            messages=conversation,
            tools=tools,
            tool_choice="auto",
        )

        message = response.choices[0].message
        if message.tool_calls:
            conversation.append(
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [c.model_dump() for c in message.tool_calls],
                }
            )
            for call in message.tool_calls:
                try:
                    args = json.loads(call.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}

                if call.function.name == "write_file":
                    result = write_file(PathArg(path=args.get("path", "")), args.get("content", ""))
                elif call.function.name == "read_file":
                    result = read_file(PathArg(path=args.get("path", "")))
                elif call.function.name == "list_files":
                    result = list_files()
                elif call.function.name == "run_cmd":
                    result = run_cmd(Cmd(cmd=args.get("cmd", "")))
                else:
                    result = f"Unknown tool: {call.function.name}"

                conversation.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": result,
                    }
                )
        else:
            return [message.content] if message.content else []


def main() -> None:
    """CLI entry point for the MCP dev-ops tools server."""
    load_dotenv()
    parser = argparse.ArgumentParser(description="Run MCP tools server")
    parser.add_argument("--model", default="meta-llama/llama-4-maverick-17b-128e-instruct")
    parser.add_argument("--port", type=int, default=4876)
    parser.add_argument(
        "--transport",
        choices=["streamable-http", "sse"],
        default="streamable-http",
        help="Transport to use (default: streamable-http)",
    )
    args = parser.parse_args()

    ensure_sandbox()
    banner = textwrap.dedent(
        f"""
        Running MCP dev-ops tools server
        Model : {args.model}
        Port  : {args.port}
        Sandbox: {SANDBOX}
        """
    ).strip()
    print(banner)

    # Configure and run the FastMCP server
    app.settings.port = args.port
    app.run(args.transport)


if __name__ == "__main__":
    main()
