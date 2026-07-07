# How Tools Work in the Strands SDK

**Date:** 2026-01-31
**Context:** SDK Fundamentals - Learning Guide
**Source Files:** `src/strands/tools/decorator.py`, `src/strands/tools/registry.py`, `src/strands/types/tools.py`, `src/strands/tools/executors/`

---

## 1. What Is a Tool?

A tool is a Python function that the AI model can call during a conversation.

**Plain English:** When you chat with an agent, the model (Claude, GPT, etc.) can only generate text on its own. But sometimes it needs to *do* things -- check the weather, read a file, query a database. Tools give it that ability.

**Analogy:** Imagine the AI is a person sitting in a room with no windows. On the wall, there are labeled buttons: "Check Weather", "Send Email", "Search Database". The AI reads the labels, decides which button to press based on the conversation, pushes it, reads the result that comes back on a screen, and then continues the conversation. Each button is a tool.

The important thing: the AI does not run the tool itself. It *requests* that a tool be run with specific inputs, and the SDK handles the actual execution.

---

## 2. The @tool Decorator

The `@tool` decorator is the simplest way to create a tool. It transforms a plain Python function into an `AgentTool` object.

**Source:** `src/strands/tools/decorator.py`

### What It Does

When you write `@tool` above a function, the decorator:

1. Reads the function **name** (becomes the tool name)
2. Reads the **docstring** (becomes the tool description)
3. Reads **parameter types and names** (becomes the input schema)
4. Generates a **JSON schema** (the `ToolSpec`) the model uses to understand the tool
5. Wraps everything into a `DecoratedFunctionTool` (which extends `AgentTool`)

### Basic Example

```python
from strands import tool

@tool
def weather_tool(city: str, units: str = "fahrenheit") -> str:
    """Get the current weather for a city.

    Args:
        city: The city name to check weather for.
        units: Temperature units, either fahrenheit or celsius.
    """
    # Your actual weather API call here
    return f"72F and sunny in {city}"
```

This single function plus `@tool` is all you need. The decorator automatically generates the following tool spec:

```json
{
    "name": "weather_tool",
    "description": "Get the current weather for a city.",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The city name to check weather for."
                },
                "units": {
                    "type": "string",
                    "description": "Temperature units, either fahrenheit or celsius.",
                    "default": "fahrenheit"
                }
            },
            "required": ["city"]
        }
    }
}
```

Notice:
- `city` is **required** (no default value)
- `units` is **optional** (has a default)
- Descriptions come from the `Args:` section of the docstring

### Using @tool With Parameters

You can customize the tool by passing arguments to the decorator:

```python
@tool(name="get_weather", description="Custom description override")
def weather_tool(city: str) -> str:
    """This docstring description gets overridden."""
    return f"72F in {city}"
```

**How it works internally** (from `decorator.py` lines 757-790):
- The decorator creates a `FunctionToolMetadata` object that inspects the function
- `FunctionToolMetadata.extract_metadata()` builds the `ToolSpec`
- A `DecoratedFunctionTool` is returned, which implements `AgentTool` but also works as a normal callable function

---

## 3. Tool Lifecycle -- 5 Stages

A tool goes through five stages from definition to execution:

### Stage 1: Definition

You define a function and decorate it with `@tool`. This creates a `DecoratedFunctionTool` object.

```python
@tool
def my_tool(x: int) -> str:
    """Does something useful."""
    return str(x * 2)
```

At this point, `my_tool` is a `DecoratedFunctionTool` instance (which is an `AgentTool`).

### Stage 2: Registration

When you pass tools to an Agent, the `ToolRegistry.process_tools()` method handles registration.

**Source:** `src/strands/tools/registry.py`, lines 45-153

```python
agent = Agent(tools=[my_tool])
# Internally: agent.tool_registry.process_tools([my_tool])
```

`process_tools` accepts many formats:
- `@tool` decorated functions (instances of `AgentTool`)
- Module import paths as strings (`"strands_tools.file_read"`)
- File paths (`"./tools/my_tool.py"`)
- `ToolProvider` instances (like MCP servers)

Each tool gets stored in the registry dict: `{tool_name: AgentTool}`.

### Stage 3: Initialization

`ToolRegistry.initialize_tools()` discovers tool modules from the `./tools/` directory (if present) and loads them.

**Source:** `src/strands/tools/registry.py`, lines 454-563

For most users passing tools directly to `Agent(tools=[...])`, this step is handled automatically. Directory-based discovery is for advanced use cases.

### Stage 4: Specification

Before calling the model, the SDK collects all tool specs and sends them alongside the messages.

**Source:** `src/strands/tools/registry.py`, lines 565-573

```python
# Inside the SDK, before calling the model:
tool_specs = agent.tool_registry.get_all_tool_specs()
# Returns: [{"name": "my_tool", "description": "...", "inputSchema": {...}}, ...]
```

The model receives these specs and knows what tools are available, what they do, and what parameters they accept.

### Stage 5: Execution

The model decides to use a tool and sends back a `ToolUse` request. The SDK's event loop receives it, looks up the tool in the registry, and calls it via the tool executor.

```
Model says: "I want to call my_tool with x=5"
  -> SDK looks up "my_tool" in ToolRegistry
  -> Calls my_tool.stream(tool_use, invocation_state)
  -> Gets result back
  -> Sends ToolResult back to model as a user message
  -> Model continues reasoning
```

---

## 4. ToolSpec -- What the Model Sees

A `ToolSpec` is a TypedDict that describes a tool to the model. It follows a JSON Schema format.

**Source:** `src/strands/types/tools.py`, lines 23-38

```python
class ToolSpec(TypedDict):
    description: str
    inputSchema: JSONSchema
    name: str
    outputSchema: NotRequired[JSONSchema]  # Not all providers support this
```

**Complete example** of what gets sent to the model:

```json
{
    "name": "search_database",
    "description": "Search a database for records matching a query.",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query string."
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return.",
                    "default": 10
                }
            },
            "required": ["query"]
        }
    }
}
```

The model reads this and knows: "There's a tool called `search_database`. It needs a `query` string and optionally a `limit` integer."

---

## 5. ToolUse -- What the Model Sends Back

When the model decides to use a tool, it sends a `ToolUse` object as part of its response.

**Source:** `src/strands/types/tools.py`, lines 53-65

```python
class ToolUse(TypedDict):
    input: Any          # The parameters the model chose
    name: str           # Which tool to call
    toolUseId: str      # Unique ID for this specific call
```

**Example of what the model sends back:**

```json
{
    "toolUseId": "tooluse_abc123",
    "name": "search_database",
    "input": {
        "query": "customers in Seattle",
        "limit": 5
    }
}
```

This appears as a `toolUse` content block inside the assistant's message. One assistant message can contain multiple `toolUse` blocks (the model can request several tools at once).

---

## 6. ToolResult -- What Goes Back to the Model

After the SDK executes the tool, it wraps the result in a `ToolResult` and sends it back to the model as a **user message**.

**Source:** `src/strands/types/tools.py`, lines 88-99

```python
class ToolResult(TypedDict):
    content: list[ToolResultContent]   # The actual result data
    status: ToolResultStatus           # "success" or "error"
    toolUseId: str                     # Matches the original ToolUse ID
```

**Example of a successful result:**

```json
{
    "toolUseId": "tooluse_abc123",
    "status": "success",
    "content": [
        {"text": "Found 3 customers in Seattle: Alice, Bob, Carol"}
    ]
}
```

**Example of an error result:**

```json
{
    "toolUseId": "tooluse_abc123",
    "status": "error",
    "content": [
        {"text": "Error: DatabaseConnectionError - Connection timed out"}
    ]
}
```

Key detail: the `ToolResult` is wrapped in a **user message** and added to the conversation. This is how the model "reads" the result -- it appears in the message history as if the user said it. The model then uses this information to continue reasoning or generate a final answer.

---

## 7. ToolContext -- Giving Tools Access to the Agent

Sometimes a tool needs more than just its input parameters. It might need access to the agent itself, the conversation history, or shared state. That is what `ToolContext` provides.

**Source:** `src/strands/types/tools.py`, lines 128-160

```python
@dataclass
class ToolContext(_Interruptible):
    tool_use: ToolUse                # The ToolUse that triggered this call
    agent: Any                       # The Agent instance running this tool
    invocation_state: dict[str, Any] # Shared state across the invocation
```

### How to Use It

Enable context by setting `context=True` on the decorator:

```python
from strands import tool
from strands.types.tools import ToolContext

@tool(context=True)
def smart_tool(query: str, tool_context: ToolContext) -> str:
    """A tool that can access agent state.

    Args:
        query: The search query.
    """
    # Access the agent
    agent = tool_context.agent

    # Access conversation history
    message_count = len(agent.messages)

    # Access the tool_use that triggered this call
    tool_id = tool_context.tool_use["toolUseId"]

    # Access shared invocation state (passed when calling agent)
    session_id = tool_context.invocation_state.get("session_id", "none")

    # You can even trigger an interrupt for human-in-the-loop
    # tool_context.interrupt("confirm_action")

    return f"Processed '{query}' (messages: {message_count}, session: {session_id})"
```

The parameter **must** be named `tool_context` by default (or you can customize it with `context="my_param_name"`). It is automatically excluded from the tool's input schema -- the model never sees it.

### Common Use Cases for ToolContext

| Use Case | What You Access |
|---|---|
| Sub-agent calls | `tool_context.agent` to invoke nested agents |
| Conversation awareness | `tool_context.agent.messages` to read history |
| Human-in-the-loop | `tool_context.interrupt("approval")` to pause for user input |
| Shared state | `tool_context.invocation_state` for cross-tool data passing |
| Tool identity | `tool_context.tool_use["toolUseId"]` for tracking |

---

## 8. Parallel vs Sequential Execution

When the model requests multiple tools at once, the SDK can execute them either concurrently or sequentially.

**Source:** `src/strands/tools/executors/__init__.py`

### Default: Concurrent Execution

By default, the SDK uses `ConcurrentToolExecutor`, which runs tools in parallel using `asyncio.create_task()`.

```python
from strands import Agent

# Default -- tools run concurrently
agent = Agent(tools=[tool_a, tool_b, tool_c])
```

If the model requests `tool_a`, `tool_b`, and `tool_c` in the same response, all three start executing at roughly the same time.

### Sequential Execution

If your tools have dependencies or side effects that require ordering, use the sequential executor:

```python
from strands import Agent
from strands.tools.executors import SequentialToolExecutor

agent = Agent(
    tools=[tool_a, tool_b, tool_c],
    tool_executor=SequentialToolExecutor()
)
```

Now `tool_a` finishes before `tool_b` starts, and `tool_b` finishes before `tool_c` starts.

### When to Use Each

| Executor | Use When |
|---|---|
| `ConcurrentToolExecutor` (default) | Tools are independent (API calls, lookups) |
| `SequentialToolExecutor` | Tools have side effects or depend on shared state |

---

## 9. The ToolRegistry

The `ToolRegistry` is the central storage for all tools available to an agent. Think of it as a dictionary: `{tool_name: AgentTool}`.

**Source:** `src/strands/tools/registry.py`

### Key Attributes

```python
class ToolRegistry:
    registry: dict[str, AgentTool]        # All registered tools
    dynamic_tools: dict[str, AgentTool]   # Dynamically loaded tools
    tool_config: dict[str, Any] | None    # Cached tool configuration
```

### Key Methods

| Method | What It Does |
|---|---|
| `process_tools(tools)` | Takes a list of tools in any format and registers them |
| `register_tool(tool)` | Registers a single `AgentTool` |
| `get_all_tool_specs()` | Returns list of `ToolSpec` dicts for all tools |
| `get_all_tools_config()` | Returns validated tool configs for model API calls |
| `register_dynamic_tool(tool)` | Registers a tool at runtime (after agent creation) |
| `replace(new_tool)` | Swaps an existing tool's implementation |
| `reload_tool(tool_name)` | Reloads a tool from disk (hot reload) |
| `validate_tool_spec(spec)` | Validates a tool spec has required fields |
| `cleanup()` | Cleans up tool providers (MCP connections, etc.) |

### Dynamic Tool Add/Remove

You can modify tools after agent creation:

```python
agent = Agent(tools=[tool_a])

# Add a new tool at runtime
@tool
def tool_b(x: int) -> str:
    """New tool."""
    return str(x)

agent.tool_registry.register_tool(tool_b)

# Replace an existing tool
@tool
def tool_a(x: int) -> str:
    """Updated implementation."""
    return str(x * 10)

agent.tool_registry.replace(tool_a)
```

### Duplicate Name Protection

The registry prevents registering two tools with the same name (lines 243-263):
- Exact duplicate names raise `ValueError`
- Names that differ only by `-` vs `_` (e.g., `my-tool` vs `my_tool`) also raise `ValueError`
- Exception: tools with `supports_hot_reload = True` can overwrite themselves

---

## Quick Reference

```
@tool decorator
    |
    v
DecoratedFunctionTool (AgentTool)
    |
    v
ToolRegistry.process_tools()  -->  registry dict {name: AgentTool}
    |
    v
ToolRegistry.get_all_tool_specs()  -->  [ToolSpec, ToolSpec, ...]  (sent to model)
    |
    v
Model returns ToolUse  -->  event loop looks up tool  -->  executor calls tool
    |
    v
ToolResult  -->  wrapped as user message  -->  sent back to model
```

**Key source files:**
- `src/strands/tools/decorator.py` -- `@tool` decorator, `DecoratedFunctionTool`, `FunctionToolMetadata`
- `src/strands/tools/registry.py` -- `ToolRegistry` class
- `src/strands/types/tools.py` -- `ToolSpec`, `ToolUse`, `ToolResult`, `ToolContext`, `AgentTool`
- `src/strands/tools/executors/concurrent.py` -- `ConcurrentToolExecutor`
- `src/strands/tools/executors/sequential.py` -- `SequentialToolExecutor`
