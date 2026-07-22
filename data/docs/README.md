# 🔌 Model Context Protocol (MCP) — Complete Guide

A practical, all-in-one reference for understanding and building with the **Model Context Protocol (MCP)** — Anthropic's open standard for connecting AI models to external tools, data, and systems.

<p align="left">
  <img src="https://img.shields.io/badge/Protocol-JSON--RPC%202.0-blue" alt="JSON-RPC 2.0"/>
  <img src="https://img.shields.io/badge/SDK-FastMCP-orange" alt="FastMCP"/>
  <img src="https://img.shields.io/badge/Debug-MCP%20Inspector-green" alt="MCP Inspector"/>
  <img src="https://img.shields.io/badge/Language-Python-yellow" alt="Python"/>
</p>

---

## 📚 Table of Contents

1. [What is MCP?](#1-what-is-mcp)
2. [Core Concepts](#2-core-concepts)
   - [2.1 MCP Server](#21-mcp-server)
   - [2.2 MCP Client](#22-mcp-client)
   - [2.3 Transport](#23-transport)
   - [2.4 Sampling](#24-sampling)
   - [2.5 Elicitation](#25-elicitation)
   - [2.6 Roots](#26-roots)
3. [Sampling vs Elicitation — Don't Confuse Them](#3-sampling-vs-elicitation--dont-confuse-them)
4. [Important Imports Explained](#4-important-imports-explained)
5. [MCP Inspector — Setup & Usage](#5-mcp-inspector--setup--usage)
6. [Quick Recap Table](#6-quick-recap-table)
7. [Summary Cheat Sheet](#7-summary-cheat-sheet)
8. [What to Practice Next](#8-what-to-practice-next)

---

## 1. What is MCP?

Think of MCP as a **"USB-C port" for AI models**.

Before MCP, every AI application that wanted to connect to tools or data (Slack, GitHub, a local database, a filesystem) needed its own custom, one-off glue code. This is often called the **"N×M integration problem"** — N models × M tools = N custom integrations for every single tool.

MCP solves this with a single, standardized protocol:

```
 AI Application (Host)  <──MCP──>  MCP Server  <──>  External System
   e.g. Claude Desktop               e.g. GitHub server      e.g. GitHub API
```

Once a tool exposes an MCP server, **any** MCP-compatible client (Claude Desktop, Claude Code, your own app) can use it — no custom integration required. Client and server talk to each other using **JSON-RPC 2.0** as the underlying message protocol.

### Key Benefits

- 🔄 **Standardization** — one protocol instead of N×M custom integrations
- ♻️ **Reusability** — write a server once, use it from any MCP client
- 🧩 **Separation of concerns** — the model doesn't need to know API details; the server handles that
- 🔒 **Security boundary** — servers control exactly what's exposed to the model

<details>
<summary><strong>🍽️ Restaurant Analogy (click to expand)</strong></summary>
<br>

| Term | Role | Analogy |
|---|---|---|
| **MCP Server** | Exposes tools/resources/prompts | The restaurant **kitchen** — has a menu (tools), takes orders |
| **MCP Client** | Connects to a server and uses its capabilities | The **waiter** — takes the order to the kitchen, brings food back |
| **Host** | The actual application running the client | The **restaurant itself** (Claude Desktop, your app) |

</details>

### MCP Architecture (3 Pieces)

| Component | Role |
|---|---|
| **Host** | The AI application the user interacts with (Claude Desktop, an IDE, your custom app) |
| **Client** | Lives inside the host; maintains a 1:1 connection with a server |
| **Server** | A lightweight program exposing specific capabilities (tools, resources, prompts) |

---

## 2. Core Concepts

MCP defines a few core building blocks. Each has a clear, single responsibility.

### 2.1 MCP Server

A server exposes capabilities to clients. It's typically small and focused — e.g. a "GitHub server," "filesystem server," or "database server."

```python
from mcp.server.fastmcp import FastMCP

# Create a server instance and give it an identity
mcp = FastMCP("weather-server")

@mcp.tool()
def get_weather(city: str) -> str:
    """Get current weather for a city."""   # <- docstring = tool description the LLM reads
    return f"The weather in {city} is sunny, 28°C."

@mcp.resource("config://app-settings")
def get_settings() -> str:
    """Expose read-only application settings."""
    return "theme=dark;lang=en"

@mcp.prompt()
def review_code(code: str) -> str:
    """A reusable prompt template."""
    return f"Please review this code for bugs:\n\n{code}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

| Line | Why it matters |
|---|---|
| `FastMCP("weather-server")` | Gives the server an identity name the client can recognize |
| `@mcp.tool()` | Registers a function so the AI model can call it |
| Docstring inside a tool | **Critical.** The LLM reads this to decide *when* to use the tool. A missing docstring causes confusion or broken schema generation |
| `@mcp.resource()` | Read-only data — not an "action" like a tool, just data (file content, config, DB row) |
| `@mcp.prompt()` | A reusable prompt template the client can request |
| `mcp.run(transport=...)` | Defines what kind of connection the server accepts |

**When to use it:** build a server whenever you need to expose a custom tool or data source (an internal API, company DB, filesystem) to *any* MCP-compatible AI client.

### 2.2 MCP Client

The client lives inside the host application. It connects to exactly **one** server, handles the handshake, and forwards requests/responses.

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="python",
    args=["weather_server.py"],
)

async def main():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()          # handshake — must run first

            tools = await session.list_tools()   # discover tools dynamically
            print(tools)

            result = await session.call_tool("get_weather", {"city": "Bengaluru"})
            print(result)

            resources = await session.list_resources()
            data = await session.read_resource("config://app-settings")
```

| Line | Why it matters |
|---|---|
| `StdioServerParameters(...)` | Tells the client how to launch the server as a subprocess |
| `stdio_client(...)` | Opens the connection, returns `(read, write)` streams |
| `ClientSession` | The object that handles the actual JSON-RPC conversation |
| `session.initialize()` | **Handshake step** — client and server exchange supported capabilities. Skipping this breaks every later call |
| `list_tools()` | Discovers available tools dynamically (never hardcode them) |
| `call_tool(name, args)` | Invokes a tool, passing arguments as a dictionary |

**When to use it:** if you're building an AI application that needs to connect to multiple MCP servers (GitHub, Slack, a custom server), you write client code — or you rely on a host that already has one built in, like Claude Desktop or Claude.ai.

### 2.3 Transport

Transport defines **how** messages physically move between client and server. The messages themselves are always JSON-RPC 2.0 — transport is just the delivery mechanism.

| Transport | Location | Setup | Use Case | Multiple Clients? | Latency |
|---|---|---|---|---|---|
| **stdio** | Same machine | Simple, no network config | Local tools, dev/testing | No (1 client per process) | Very low |
| **Streamable HTTP** | Local or remote | Needs host/port, maybe auth | Production, shared/remote servers | Yes | Network-dependent |
| ~~SSE (legacy)~~ | — | — | Being phased out in favor of Streamable HTTP | — | — |

**stdio (local):**
```python
mcp.run(transport="stdio")
```
The server runs as a local subprocess. The client launches it and talks over stdin/stdout pipes — no network involved. Used for local file access, local DB, CLI tools (e.g. a local server added inside Claude Desktop).

```python
from mcp.client.stdio import stdio_client, StdioServerParameters

params = StdioServerParameters(command="python", args=["server.py"])
async with stdio_client(params) as (read, write):
    ...
```

**Streamable HTTP (remote):**
```python
mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
```
The server exposes an HTTP endpoint (e.g. `http://localhost:8000/mcp`). The client sends HTTP requests and receives streaming responses. Used when a server is hosted remotely/in the cloud and needs to serve multiple teams or apps at once.

```python
from mcp.client.streamable_http import streamablehttp_client

async with streamablehttp_client("https://my-mcp-server.com/mcp") as (read, write, _):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
```

### 2.4 Sampling

**Direction: Server → Client's LLM.**

Sampling lets a **server request an LLM completion through the client** — the server "borrows" the model's intelligence without needing its own API key or model access. The client stays in control and can approve, deny, or modify the request (human-in-the-loop).

> Normally tool calls flow Client → Server. Sampling reverses that: Server → Client, asking "please have your LLM generate this for me."

```python
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("summarizer-server")

@mcp.tool()
async def summarize(text: str, ctx: Context) -> str:
    """Ask the client's LLM to summarize text."""
    response = await ctx.session.create_message(
        messages=[{"role": "user", "content": {"type": "text", "text": f"Summarize: {text}"}}],
        max_tokens=200,
    )
    return response.content.text
```

**When to use it:** the server needs some AI reasoning (summarizing, classifying) but doesn't hold a standalone LLM connection — so it borrows the client's model instead.

### 2.5 Elicitation

**Direction: Server → User (via the client).**

Elicitation lets a **server ask the user for additional input mid-operation** — for example, confirming an action or requesting missing information before it can finish a task.

```python
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("booking-server")

@mcp.tool()
async def book_flight(destination: str, ctx: Context) -> str:
    """Book a flight, confirming with the user first."""
    response = await ctx.elicit(
        message="Which date would you like to travel?",
        schema={"type": "string", "format": "date"}
    )
    if response.action == "accept":
        travel_date = response.content
        return f"Booking flight to {destination} on {travel_date}"
    return "Booking cancelled — date not provided"
```

| Piece | Why it matters |
|---|---|
| `ctx.elicit(message=..., schema=...)` | Pauses execution and sends a structured question to the client |
| `schema` | Defines the expected answer type (string, date, enum, etc.) — like form validation |
| `response.action` | Tells you whether the user accepted, declined, or cancelled |

**When to use it:** multi-step workflows where not all information is available upfront and you need mid-task user input — bookings, form filling, confirmations.

### 2.6 Roots

**Direction: Client → Server.**

Roots let the **client tell the server what its access boundary is** — which directories or URIs it's allowed to operate within, and nothing outside that.

> Think of hiring a contractor to work on your house. You tell them: "This is your work area — kitchen and hall only, don't go into the bedroom." That boundary is a **root**.

```python
from mcp.types import Root

# Client declares roots when initializing
roots = [
    Root(uri="file:///home/user/project", name="My Project"),
    Root(uri="file:///home/user/documents", name="Documents"),
]

await session.initialize()

# Server can then discover the allowed scope:
available_roots = await session.list_roots()
```

| Piece | Why it matters |
|---|---|
| `Root(uri=..., name=...)` | Defines one specific directory/location the server may access |
| Declared at `initialize()` | The client communicates the boundary right when the session starts |
| `list_roots()` | The server calls this to discover — and respect — its allowed scope |

**When to use it:** filesystem-based servers, where you want to restrict access to specific folders instead of granting access to an entire disk — a security and scoping mechanism.

---

## 3. Sampling vs Elicitation — Don't Confuse Them

| | Sampling | Elicitation |
|---|---|---|
| **Server asks…** | The client's LLM, for generation | The human user, for info/confirmation |
| **Purpose** | AI reasoning / text generation | Missing data / confirmation |
| **Example** | "Summarize this for me" | "What date do you want?" |

---

## 4. Important Imports Explained

| Import | What it does |
|---|---|
| **`FastMCP`** (`mcp.server.fastmcp`) | High-level, decorator-based API for building MCP servers quickly. Handles boilerplate (protocol handshake, schema generation from type hints) so you just write `@mcp.tool()`, `@mcp.resource()`, `@mcp.prompt()` functions |
| **`ClientSession`** (`mcp`) | The core client-side object. Wraps a read/write stream pair and gives high-level methods: `initialize()`, `list_tools()`, `call_tool()`, `list_resources()`, `read_resource()`, `list_prompts()`, `get_prompt()` |
| **`StdioServerParameters`** (`mcp`) | Config object describing how to launch a local server as a subprocess — command, arguments, environment variables. Passed into `stdio_client()` |
| **`stdio_client`** (`mcp.client.stdio`) | Async context manager that spawns the server subprocess and returns `(read, write)` streams. Used for **local** servers |
| **`streamablehttp_client`** (`mcp.client.streamable_http`) | Async context manager that connects to a **remote** MCP server over HTTP(S), returning `(read, write, get_session_id)` streams. Used for **deployed/hosted** servers |
| **`Context`** (`mcp.server.fastmcp`) | Passed into tool functions to give access to session-level features — logging, progress reporting, elicitation (`ctx.elicit`), sampling (`ctx.session.create_message`) |
| **`Tool` / `Resource` / `Prompt`** (`mcp.types`) | Underlying Pydantic data models representing what a tool, resource, or prompt looks like on the wire — mostly relevant below the FastMCP abstraction layer |
| **`Root`** (`mcp.types`) | Data model representing an access-boundary declaration made by the client |
| **`mcp.run(transport=...)`** | Server-side entry point that starts listening — `transport="stdio"` for local, `transport="streamable-http"` for remote-hosted servers |

### Quick Mental Model

```
Server side:  FastMCP  →  @mcp.tool()/@mcp.resource()/@mcp.prompt()  →  mcp.run(transport=...)
Client side:  stdio_client() or streamablehttp_client()  →  (read, write) streams  →  ClientSession
```

---

## 5. MCP Inspector — Setup & Usage

**MCP Inspector** is Anthropic's official browser-based debugging tool for MCP servers. It lets you test tools, resources, and prompts **without needing a full client** like Claude Desktop — great for development and debugging.

### 5.1 Running Inspector

No installation needed — run it directly with `npx`:

```bash
npx @modelcontextprotocol/inspector python your_server.py
```

This will:
1. Launch your MCP server as a subprocess (via stdio)
2. Start a local web UI (usually at `http://localhost:6274`)
3. Open your browser to the Inspector interface

### 5.2 For Servers with Dependencies (using `uv`)

```bash
npx @modelcontextprotocol/inspector uv run python your_server.py
```

### 5.3 Inspecting a Remote (HTTP) Server

```bash
npx @modelcontextprotocol/inspector
```
Then, in the Inspector UI, manually enter the server's URL and select **Streamable HTTP** as the transport type, instead of launching a local process.

### 5.4 What You Can Do Inside Inspector

| Tab | Purpose |
|---|---|
| **Tools** | List all tools, view their auto-generated JSON schemas, and call them with test inputs |
| **Resources** | Browse and read exposed resources |
| **Prompts** | View and test prompt templates with sample arguments |
| **Notifications** | See real-time logs, progress updates, and errors from the server |

### 5.5 Typical Debugging Workflow

1. Write/update your server code (`your_server.py`)
2. Run `npx @modelcontextprotocol/inspector python your_server.py`
3. In the **Tools** tab, click **List Tools** to confirm your tool is registered correctly
4. Click a tool, fill in sample parameters, and click **Run Tool**
5. Check the response and the **Notifications** panel for errors
6. Fix issues, restart Inspector, repeat

<details>
<summary><strong>⚠️ Common Gotchas (click to expand)</strong></summary>
<br>

- Missing **docstrings** on `@mcp.tool()` functions can cause schema generation issues — always document your tools.
- If Inspector can't connect, double-check the `command`/`args` match exactly how you'd run the script from the terminal.
- For `uv`-managed projects, always launch via `uv run ...` inside the Inspector command so the correct virtual environment is used.
- Newer Inspector versions (v0.14+) require session-token authentication — check the terminal output for the token/URL Inspector prints on startup.

</details>

---

## 6. Quick Recap Table

| Concept | Direction | Purpose | Analogy |
|---|---|---|---|
| **Server** | — | Hosts tools/resources/prompts | Kitchen |
| **Client** | — | Connects to a server and uses it | Waiter |
| **stdio** | Local | Same-machine communication | Intercom |
| **Streamable HTTP** | Network | Remote/shared communication | Phone call |
| **Sampling** | Server → Client's LLM | AI text generation | "Ask your chef for me" |
| **Elicitation** | Server → User | Missing info/confirmation | "Ask the customer directly" |
| **Roots** | Client → Server | Defines the access boundary | "This is your work area" |

---

## 7. Summary Cheat Sheet

```
MCP = standard protocol connecting AI models ↔ external tools/data

Server      → exposes tools/resources/prompts     (FastMCP)
Client      → connects to ONE server               (ClientSession)
Transport   → stdio (local) or Streamable HTTP (remote)
Sampling    → server asks client's LLM for a completion
Elicitation → server asks user for input mid-task
Roots       → client tells server its access boundary

Debug everything with: npx @modelcontextprotocol/inspector <run-command>
```

---

## 8. What to Practice Next

- [ ] Build a small FastMCP server with at least one tool, one resource, and one prompt
- [ ] Connect to it with MCP Inspector and confirm the schema is generated correctly
- [ ] Write a minimal client using `stdio_client` + `ClientSession`
- [ ] Add a sampling-based tool (e.g. a summarizer that borrows the client's LLM)
- [ ] Add an elicitation flow for a multi-step task (e.g. a booking tool)
- [ ] Deploy a server with `transport="streamable-http"` and connect Inspector to it remotely
- [ ] Experiment with `Root` declarations to scope a filesystem server's access

---

<p align="center"><i>Built as a personal learning reference while working through Anthropic's "Introduction to MCP" certification and hands-on FastMCP projects.</i></p>
