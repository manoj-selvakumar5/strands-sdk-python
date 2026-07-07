# Strands Protocol Integration Guide

A comprehensive guide to Strands SDK's protocol integration capabilities, covering Agent-to-Agent (A2A) and Model Context Protocol (MCP) support.

---

## Table of Contents

1. [A2A (Agent-to-Agent) Protocol](#a2a-agent-to-agent-protocol)
2. [MCP (Model Context Protocol)](#mcp-model-context-protocol)
3. [Comparison and Use Cases](#comparison-and-use-cases)

---

# A2A (Agent-to-Agent) Protocol

## Overview

Strands SDK implements the **Agent-to-Agent (A2A) protocol** - a standardized communication protocol developed by Google that enables different AI agents to discover and interact with each other. A2A allows Strands agents to be exposed as HTTP services that other agents can call.

**Official A2A Documentation**: https://google-a2a.github.io/A2A/latest/

**Status**: Experimental (expect breaking changes)

## Core Components

### 1. A2AServer

**Location**: `src/strands/multiagent/a2a/server.py:26`

The main wrapper that converts a Strands Agent into an A2A-compatible HTTP server.

**Key Features:**
- Wraps any Strands Agent with A2A protocol support
- Exposes agents via HTTP using FastAPI or Starlette
- Publishes an **AgentCard** - metadata describing the agent's capabilities
- Supports streaming responses
- Handles load balancer deployments with path mounting

**Basic Example:**

```python
from strands import Agent
from strands.multiagent.a2a import A2AServer

# Create a Strands agent
agent = Agent(
    name="Weather Agent",
    description="Provides weather information",
    tools=[weather_tool]
)

# Wrap it with A2A protocol
a2a_server = A2AServer(
    agent,
    host="0.0.0.0",
    port=9000,
    version="1.0.0"
)

# Start the server (FastAPI or Starlette)
a2a_server.serve(app_type="fastapi")
```

### 2. StrandsA2AExecutor

**Location**: `src/strands/multiagent/a2a/executor.py:38`

The execution engine that:
- Converts **A2A protocol messages** → **Strands ContentBlocks**
- Executes the agent with streaming support
- Converts **Strands agent responses** → **A2A events**
- Handles task state management

**Message Conversion:**

| A2A Type | Strands ContentBlock |
|----------|---------------------|
| TextPart | `ContentBlock(text=...)` |
| FilePart (Image) | `ContentBlock(image=ImageContent(...))` |
| FilePart (Video) | `ContentBlock(video=VideoContent(...))` |
| FilePart (Document) | `ContentBlock(document=DocumentContent(...))` |
| DataPart | `ContentBlock(text=JSON representation)` |

## Agent Discovery Mechanism

### AgentCard

Every A2A agent publishes an **AgentCard** at `/.well-known/agent.json` containing:

```json
{
  "name": "Weather Agent",
  "description": "Provides weather information",
  "url": "http://my-server.com:9000/",
  "version": "1.0.0",
  "skills": [
    {
      "name": "get_weather",
      "id": "get_weather",
      "description": "Get current weather for a location",
      "tags": []
    }
  ],
  "default_input_modes": ["text"],
  "default_output_modes": ["text"],
  "capabilities": {
    "streaming": true
  }
}
```

### Skills Auto-Discovery

**Tools → Skills**: Strands automatically converts agent tools into A2A skills. Each tool becomes a discoverable skill that other agents can invoke.

```python
# Tools are automatically exposed as skills
agent = Agent(tools=[calculator, weather, file_reader])
a2a_server = A2AServer(agent)

# Skills are auto-generated from tools:
# - calculator → AgentSkill(name="calculator", ...)
# - weather → AgentSkill(name="weather", ...)
# - file_reader → AgentSkill(name="file_reader", ...)
```

**Custom Skills:**

```python
from a2a.types import AgentSkill

custom_skills = [
    AgentSkill(
        name="data_analysis",
        id="data_analysis",
        description="Analyzes datasets and generates insights",
        tags=["analytics", "data"]
    )
]

a2a_server = A2AServer(agent, skills=custom_skills)
```

## Deployment Scenarios

### 1. Simple Local Deployment

```python
a2a_server = A2AServer(
    agent,
    host="127.0.0.1",
    port=9000
)
a2a_server.serve()
# Available at: http://127.0.0.1:9000/
```

### 2. Load Balancer with Path Preservation

```python
a2a_server = A2AServer(
    agent,
    http_url="http://my-alb.amazonaws.com/agent1"
)
# Public URL: http://my-alb.amazonaws.com/agent1/
# Server mounts at: /agent1
# AgentCard URL: http://my-alb.amazonaws.com/agent1/.well-known/agent.json
```

### 3. Load Balancer with Path Stripping

```python
a2a_server = A2AServer(
    agent,
    http_url="http://my-alb.amazonaws.com/agent1",
    serve_at_root=True  # ALB strips /agent1 prefix
)
# Public URL: http://my-alb.amazonaws.com/agent1/
# Server serves at: / (root)
# AgentCard still advertises: http://my-alb.amazonaws.com/agent1/
```

### 4. Containerized Deployment

Supports Docker, Kubernetes, ECS, etc. with volume mounts and configurable endpoints.

## Data Handling Features

### FileParts & DataParts Support

The A2A executor handles multiple data types:

**FileParts (Images, Videos, Documents):**

```python
# A2A FilePart → Strands ContentBlock conversion
# Supports: MIME type detection, format mapping, byte/URI handling

# Image
FilePart(file=FileWithBytes(
    bytes=image_bytes,
    mime_type="image/jpeg",
    name="photo.jpg"
))
→ ContentBlock(image=ImageContent(format="jpeg", source=bytes))

# Video
FilePart(file=FileWithBytes(
    bytes=video_bytes,
    mime_type="video/mp4"
))
→ ContentBlock(video=VideoContent(format="mp4", source=bytes))

# Document
FilePart(file=FileWithBytes(
    bytes=pdf_bytes,
    mime_type="application/pdf"
))
→ ContentBlock(document=DocumentContent(format="pdf", source=bytes))
```

**DataParts (Structured Data):**

```python
# Structured JSON data
DataPart(data={"temperature": 72, "units": "F"})
→ ContentBlock(text="[Structured Data]\n{\"temperature\": 72, \"units\": \"F\"}")
```

## Advanced Configuration

### Custom Request Handler

```python
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore

a2a_server = A2AServer(
    agent,
    task_store=InMemoryTaskStore(),  # Custom task persistence
    queue_manager=custom_queue,       # Custom queue implementation
    push_config_store=custom_store,   # Push notification config
    push_sender=custom_sender         # Push notification sender
)
```

### Application Framework Choice

**FastAPI** (more features, auto docs):

```python
app = a2a_server.to_fastapi_app()
# Or
a2a_server.serve(app_type="fastapi")
```

**Starlette** (lightweight, faster):

```python
app = a2a_server.to_starlette_app()
# Or
a2a_server.serve(app_type="starlette")  # Default
```

## Protocol Flow

### Incoming Request Flow

```
1. Client → A2A Server (HTTP POST with A2A message)
   ├─ Message contains: TextPart, FilePart, or DataPart

2. A2AServer → StrandsA2AExecutor
   ├─ Convert A2A Parts → Strands ContentBlocks

3. StrandsA2AExecutor → Strands Agent
   ├─ Execute agent.stream_async(content_blocks)

4. Strands Agent → Stream Events
   ├─ {'data': 'chunk'} → TaskState.working + text message
   ├─ {'result': AgentResult} → Final artifact + complete

5. Stream Events → A2A Events → Client
   └─ Real-time streaming response
```

### Response Streaming

The executor provides **real-time streaming**:

```python
async for event in agent.stream_async(input):
    if "data" in event:
        # Incremental text chunks
        await updater.update_status(
            TaskState.working,
            new_agent_text_message(event["data"])
        )
    elif "result" in event:
        # Final result
        await updater.add_artifact(
            [Part(root=TextPart(text=str(result)))]
        )
        await updater.complete()
```

## Key Features (August 2025)

1. **FileParts and DataParts support** (#596)
   - Enhanced multimodal data handling
   - Image, video, document support
   - Structured JSON data support

2. **Tools as skills** (#287)
   - Automatic tool → skill conversion
   - Reusable capabilities across agents
   - Skill-based agent discovery

3. **Containerized deployment support** (#524)
   - Docker/Kubernetes compatibility
   - Volume mounts support
   - Load balancer integration

4. **Configurable request handler** (#601)
   - Custom task stores
   - Custom queue managers
   - Push notification support

## Limitations

- **Cancellation not supported**: The `cancel()` method raises `UnsupportedOperationError`
- **Streaming required**: A2A executor uses streaming mode exclusively
- **Experimental status**: A2A integration is marked as experimental with potential breaking changes

## Use Cases

1. **Multi-agent orchestration**: Different specialized agents communicate via A2A
2. **Agent marketplace**: Publish and discover agents via AgentCards
3. **Distributed systems**: Deploy agents across microservices
4. **Cross-platform integration**: Connect agents built with different frameworks
5. **Cloud deployments**: AWS ECS/EKS, Azure AKS, GCP Cloud Run with load balancers

---

# MCP (Model Context Protocol)

## Overview

Strands SDK provides comprehensive integration with the **Model Context Protocol (MCP)** - a protocol that enables AI agents to seamlessly connect with external tools, resources, and data sources through standardized server interfaces.

**Official MCP Documentation**: https://modelcontextprotocol.io/
**Anthropic Announcement**: https://www.anthropic.com/news/model-context-protocol

**Location**: `src/strands/tools/mcp/`

## Core Architecture

### MCPClient: Connection Manager

**Location**: `src/strands/tools/mcp/mcp_client.py:55`

The cornerstone of MCP integration in Strands. It provides:

- **Background Thread Management**: Runs MCP communication in a separate thread
- **Context Manager Pattern**: Ensures proper resource cleanup
- **Transport Abstraction**: Supports multiple communication protocols
- **Timeout Control**: Configurable startup and execution timeouts

**Architecture Diagram:**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Strands       │    │    MCPClient     │    │   MCP Server    │
│   Agent         │◄──►│                  │◄──►│                 │
│                 │    │ Background Thread│    │  Tools/Prompts  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
        │                       │                       │
        │                   Transport                   │
        └───────────────────────┼───────────────────────┘
                           stdio/SSE/HTTP
```

### MCPAgentTool: Tool Adapter

**Location**: `src/strands/tools/mcp/mcp_agent_tool.py:23`

Adapter class that wraps MCP tools and exposes them as Strands AgentTools:

- Converts MCP tool specifications to Strands ToolSpec format
- Handles synchronous and asynchronous tool execution
- Supports structured output schemas
- Manages tool result conversion

## Basic Usage

### Creating an MCP Client

```python
from strands import Agent
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters

# Create MCP client
aws_docs_client = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(
            command="uvx",
            args=["awslabs.aws-documentation-mcp-server@latest"]
        )
    ),
    startup_timeout=60  # Optional: default is 30 seconds
)

# Use with context manager
with aws_docs_client:
    # List available tools
    tools = aws_docs_client.list_tools_sync()

    # Create agent with MCP tools
    agent = Agent(tools=tools)

    # Use the agent
    response = agent("Tell me about Amazon Bedrock and how to use it with Python")
```

## Tool Discovery and Execution

### Synchronous Tool Operations

```python
with mcp_client:
    # List tools with pagination
    tools_page1 = mcp_client.list_tools_sync()
    tools_page2 = mcp_client.list_tools_sync(
        pagination_token=tools_page1.token
    )

    # Call a tool synchronously
    result = mcp_client.call_tool_sync(
        tool_use_id="unique-id",
        name="tool_name",
        arguments={"param": "value"},
        read_timeout_seconds=timedelta(seconds=30)
    )
```

### Asynchronous Tool Operations

```python
# Async tool execution (NEW in August 2025)
async def execute_tools():
    with mcp_client:
        # Execute multiple tools concurrently
        tasks = [
            mcp_client.call_tool_async(
                tool_use_id=f"task-{i}",
                name="tool_name",
                arguments={"index": i}
            )
            for i in range(5)
        ]

        results = await asyncio.gather(*tasks)
        return results
```

## Prompt Management

**NEW Feature (August 2025)** - MCP servers can provide reusable prompt templates:

```python
with mcp_client:
    # List available prompts with pagination
    prompts_result = mcp_client.list_prompts_sync()

    for prompt in prompts_result.prompts:
        print(f"{prompt.name}: {prompt.description}")

    # Get a specific prompt with arguments
    prompt_result = mcp_client.get_prompt_sync(
        prompt_id="greeting_prompt",
        args={"name": "Alice", "style": "enthusiastic"}
    )

    # Use the prompt
    for message in prompt_result.messages:
        print(message.content.text)
```

## Transport Options

### 1. stdio Transport (Most Common)

```python
from mcp import stdio_client, StdioServerParameters

client = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(
            command="uvx",
            args=["mcp-server-git"]
        )
    )
)
```

**Use Case**: Local tools, simple integrations
**Pros**: Simple setup, no network required, direct process communication
**Cons**: Single process only, no web integration

### 2. SSE (Server-Sent Events) Transport

```python
from mcp.client.sse import sse_client

client = MCPClient(
    lambda: sse_client("http://localhost:8000/sse")
)
```

**Use Case**: Web-based tools, remote servers
**Pros**: Web-compatible, real-time updates, firewall-friendly
**Cons**: Requires HTTP server, more complex setup

### 3. Streamable HTTP Transport

```python
from mcp.client.streamable_http import streamablehttp_client

client = MCPClient(
    lambda: streamablehttp_client(url="http://api.example.com/mcp")
)
```

**Use Case**: Enterprise integrations, cloud services
**Pros**: Full HTTP features, load balancing support, enterprise ready
**Cons**: Most complex setup, requires HTTP infrastructure

## Timeout Configuration

### Startup Timeout

```python
# Wait up to 60 seconds for server initialization
client = MCPClient(
    transport_callable,
    startup_timeout=60  # Default: 30 seconds
)
```

### Execution Timeout

```python
result = client.call_tool_sync(
    tool_use_id="timeout-test",
    name="slow_tool",
    arguments={"data": "..."},
    read_timeout_seconds=timedelta(seconds=120)  # 2 minutes
)
```

## Error Handling

### Initialization Errors

```python
from strands.types.exceptions import MCPClientInitializationError

try:
    client = MCPClient(transport_callable, startup_timeout=30)
    with client:
        tools = client.list_tools_sync()
except MCPClientInitializationError as e:
    print(f"Failed to initialize MCP client: {e}")
    # Handle initialization failure
```

### Tool Execution Errors

```python
def robust_tool_call(client, tool_name, arguments, max_retries=3):
    """Robust tool calling with retries"""
    for attempt in range(max_retries):
        try:
            result = client.call_tool_sync(
                tool_use_id=f"attempt-{attempt}",
                name=tool_name,
                arguments=arguments,
                read_timeout_seconds=timedelta(seconds=30)
            )

            if result['status'] == 'success':
                return result
            else:
                print(f"Attempt {attempt + 1} failed")

        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(1)  # Brief delay before retry

    return None
```

## Client Reuse Pattern

MCPClient supports reuse across multiple sessions:

```python
# Create once
reusable_client = MCPClient(transport_callable)

# Use multiple times
with reusable_client:
    result1 = reusable_client.call_tool_sync(...)

# Reuse in another context
with reusable_client:
    result2 = reusable_client.call_tool_sync(...)
```

## Integration with Strands Agents

### Basic Integration

```python
with mcp_client:
    # Get all available tools from the MCP server
    mcp_tools = mcp_client.list_tools_sync()

    # Create an agent with these tools
    agent = Agent(
        tools=mcp_tools,
        name="MCP-Enhanced Agent",
        description="Agent with MCP tool access"
    )

    # Use the agent
    response = agent("Use the available tools to help me...")
```

### Advanced Integration with Multiple Servers

```python
# Connect to multiple MCP servers
git_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(command="uvx", args=["mcp-server-git"])
))

github_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(command="uvx", args=["mcp-server-github"])
))

with git_client, github_client:
    # Combine tools from multiple servers
    all_tools = (
        git_client.list_tools_sync() +
        github_client.list_tools_sync()
    )

    # Create agent with all tools
    agent = Agent(tools=all_tools)
    response = agent("Check my git status and create a GitHub PR")
```

## Structured Content Support

MCP tools can return structured content alongside text responses:

```python
result = client.call_tool_sync(
    tool_use_id="struct-test",
    name="analyze_data",
    arguments={"dataset": "sales.csv"}
)

# Regular content
print(result['content'][0]['text'])

# Structured content (if available)
if 'structuredContent' in result:
    structured_data = result['structuredContent']
    # Process structured data
```

## Key Features Timeline

### October 2025
- **Timeout issue fixes** (#922) - Fixed MCP timeout issues for more reliable connections
- **Idempotent instrumentation** (#892) - Made MCP instrumentation idempotent to prevent recursion errors

### August 2025
- **MCP async call tool** (#406) - Async support for MCP tool execution
- **List prompts and get prompt methods** (#160) - Enhanced MCP client capabilities for prompt management
- **Pagination for list_tools_sync** (#436) - Improved handling of large tool sets
- **MCP Client configuration** (#657) - Server initialization timeout options
- **Structured content retention** (#528) - Retain structured content in AgentTool responses

## Performance Best Practices

### 1. Connection Reuse
Reuse MCPClient instances when possible to avoid initialization overhead.

### 2. Async Operations
Use `call_tool_async()` for concurrent tool calls:

```python
# Sequential (slow)
for i in range(10):
    result = client.call_tool_sync(...)

# Concurrent (fast)
tasks = [client.call_tool_async(...) for i in range(10)]
results = await asyncio.gather(*tasks)
```

### 3. Appropriate Timeouts
Set reasonable timeouts based on expected tool execution time:

```python
# Quick tools
result = client.call_tool_sync(..., read_timeout_seconds=timedelta(seconds=5))

# Long-running analysis
result = client.call_tool_sync(..., read_timeout_seconds=timedelta(minutes=5))
```

### 4. Error Handling
Implement robust error handling and retry logic for production systems.

### 5. Resource Cleanup
Always use context managers to ensure proper cleanup:

```python
# Good
with mcp_client:
    tools = mcp_client.list_tools_sync()

# Bad (may leak resources)
mcp_client.start()
tools = mcp_client.list_tools_sync()
# Forgot to call stop()
```

## OpenTelemetry Instrumentation

MCP integration includes built-in distributed tracing support:

```python
from strands.tools.mcp.mcp_instrumentation import mcp_instrumentation

# Automatically called when creating MCPClient
# Enables distributed tracing for MCP operations
```

## Real-World Examples

### AWS Documentation Server

```python
aws_client = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(
            command="uvx",
            args=["awslabs.aws-documentation-mcp-server@latest"]
        )
    ),
    startup_timeout=60
)

with aws_client:
    agent = Agent(tools=aws_client.list_tools_sync())
    response = agent("How do I configure Amazon Bedrock with Python?")
```

### Git Operations Server

```python
git_client = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(command="uvx", args=["mcp-server-git"])
    )
)

with git_client:
    agent = Agent(tools=git_client.list_tools_sync())
    response = agent("Show me the recent commits and check the status")
```

### Filesystem Server

```python
fs_client = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(command="uvx", args=["mcp-server-filesystem"])
    )
)

with fs_client:
    agent = Agent(tools=fs_client.list_tools_sync())
    response = agent("List all Python files in the current directory")
```

## Available MCP Servers

Explore the growing ecosystem of MCP servers:
- [MCP Server Registry](https://github.com/modelcontextprotocol/servers)
- AWS Documentation Server
- Git Operations Server
- GitHub Server
- Filesystem Server
- Slack Server
- PostgreSQL Server
- And hundreds more...

---

# Comparison and Use Cases

## A2A vs MCP

| Aspect | A2A (Agent-to-Agent) | MCP (Model Context Protocol) |
|--------|---------------------|------------------------------|
| **Primary Purpose** | Agent discovery and communication | Tool/resource integration |
| **Direction** | Agent ↔ Agent | Agent → Tools/Resources |
| **Protocol Type** | HTTP-based RPC | Various transports (stdio, SSE, HTTP) |
| **Discovery** | AgentCard at `/.well-known/agent.json` | Server capability negotiation |
| **Streaming** | Required | Optional |
| **Use Case** | Multi-agent systems | Tool extensibility |
| **Standardization** | Google A2A Protocol | Anthropic/Industry MCP |
| **Status in Strands** | Experimental | Stable |

## When to Use A2A

1. **Multi-agent orchestration**: When you need multiple specialized agents to collaborate
2. **Agent marketplace**: Publishing and discovering agents as services
3. **Distributed AI systems**: Deploying agents across different services/clouds
4. **Cross-framework integration**: Connecting agents built with different frameworks
5. **Autonomous agent networks**: Building systems where agents discover and call each other

**Example Scenario**: An e-commerce platform with specialized agents for inventory, customer service, fraud detection, and pricing that need to communicate and coordinate.

## When to Use MCP

1. **Tool extensibility**: Adding external tools to your agents (file systems, databases, APIs)
2. **Resource access**: Connecting agents to data sources and services
3. **Standardized integrations**: Using pre-built MCP servers from the ecosystem
4. **Development tools**: Integrating with IDEs, version control, documentation systems
5. **Enterprise integrations**: Connecting to internal systems and tools

**Example Scenario**: An AI assistant that needs to access Git repositories, query databases, read documentation, and interact with file systems.

## Combined Usage

You can use both A2A and MCP together:

```python
# MCP for tool access
git_client = MCPClient(...)
docs_client = MCPClient(...)

# Create an agent with MCP tools
with git_client, docs_client:
    all_tools = git_client.list_tools_sync() + docs_client.list_tools_sync()

    dev_agent = Agent(
        name="Developer Assistant",
        description="Helps with development tasks",
        tools=all_tools
    )

    # Expose via A2A for other agents to use
    a2a_server = A2AServer(dev_agent, port=9000)
    a2a_server.serve()
```

## Summary

- **A2A**: Use for agent-to-agent communication and multi-agent systems
- **MCP**: Use for tool and resource integration with external systems
- **Together**: Build comprehensive agentic systems with both inter-agent communication and rich tool access

Both protocols are first-class citizens in Strands SDK, enabling you to build sophisticated, interoperable, and extensible AI agent systems.

---

## Additional Resources

### A2A Resources
- [Google A2A Protocol Specification](https://google-a2a.github.io/A2A/latest/)
- [A2A GitHub Repository](https://github.com/google-a2a)

### MCP Resources
- [MCP Protocol Documentation](https://modelcontextprotocol.io/)
- [MCP Server Registry](https://github.com/modelcontextprotocol/servers)
- [Anthropic MCP Announcement](https://www.anthropic.com/news/model-context-protocol)

### Strands Documentation
- [Strands Agents Documentation](https://strandsagents.com/)
- [Latest Features](LATEST_FEATURES.md)
- [GitHub Repository](https://github.com/strands-agents/sdk-python)

---

**Last Updated**: January 2025
**Strands SDK Version**: Compatible with latest release
**Status**: A2A (Experimental), MCP (Stable)
