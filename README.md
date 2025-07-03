# groq-mcp-local-script-creation-with-no-cost

This repository demonstrates how to use **Groq's Model Control Plane (MCP)** to create and run Python scripts locally. The project exposes a simple server with several file management tools and a small agent that can call those tools using Groq's chat completion API. Example clients show how to automatically generate and execute games inside a sandbox directory.

Groq's MCP server is free to run on your own machine. Once you provide a Groq API key (the public tier currently has no cost) you can launch the server and generate scripts locally without paying for compute.

## Code Overview

- **app.py** – starts the local MCP server and registers a set of tools for
  writing, reading and executing files in the `game_lab` directory. It also
  exposes a `compound_tool` that lets Groq's language model call those tools via
  function calling.
- **snake_game.py** and **tictactoe_game.py** – example clients that connect to
  the running server, request it to generate a game script and then run it.
- **game_lab/** – sandbox directory where all generated files are written. 

## Getting Started

1. Create a virtual environment and install the requirements:

```bash
python3 -m venv mcp
source mcp/bin/activate
pip install -r requirements.txt
```

2. Provide your Groq API key:

```bash
export GROQ_API_KEY=your_key_here
```

3. Start the MCP tool server:

```bash
python app.py --transport sse
```

if you want to mention the LLM model to use

```bash
python app.py --transport sse --model meta-llama/llama-4-maverick-17b-128e-instruct
```

Leave this terminal running so the server stays active. It listens on port
`4876` by default and stores all generated files inside the `game_lab`
directory.

## Available Tools

The server registers a number of helper tools:

- **write_file** – create or overwrite a file under `game_lab`.
- **read_file** – read the contents of a file from `game_lab`.
- **list_files** – list all files in the sandbox directory.
- **run_cmd** – execute a shell command in `game_lab`.
- **compound_tool** – an agent that calls Groq's LLM, which can invoke the above tools using function calling.

These tools can be invoked through the MCP API or by using the sample clients.

## Example Clients

Two example programs are included. Each connects to the running MCP server and requests it to write and execute a simple game:

- `snake_game.py` – generates a minimal snake game and runs it for about ten seconds.
- `tictactoe_game.py` – generates a basic tic‑tac‑toe simulation.

Run either script from a separate terminal while the server is running:

```bash
python snake_game.py
python tictactoe_game.py
```

The agent writes the resulting game source files into the `game_lab` folder and
immediately runs them using the `run_cmd` tool. Once the script finishes you can
find the files in that directory and execute them again manually:

```bash
python game_lab/snake.py       # or game_lab/tictactoe.py
```

Make sure to keep the server terminal open while running the clients so the
script creation and execution can complete.

Both examples use the `compound_tool` to create game files and then run them with `run_cmd`.

## Repository Purpose

This project serves as a lightweight demonstration of how Groq's MCP can be used to automate local development tasks. By customizing the prompts or extending the available tools you can experiment with generating and executing other kinds of programs. Feel free to fork this repository and adapt it to your own workflows.