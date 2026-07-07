# A2AServer and A2AClientToolProvider - How They Work Together

## Overview

The A2A (Agent-to-Agent) protocol enables Strands agents to communicate with each other over HTTP. Two key components enable this:

1. **A2AServer** (SDK) - Exposes a Strands Agent as an A2A-compliant HTTP server
2. **A2AClientToolProvider** (Tools) - Provides tools for agents to discover and communicate with A2A servers

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ORCHESTRATOR AGENT                                 │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                     A2AClientToolProvider                               │ │
│  │  ┌─────────────────────┐ ┌─────────────────────┐ ┌──────────────────┐  │ │
│  │  │ a2a_discover_agent  │ │ a2a_list_discovered │ │ a2a_send_message │  │ │
│  │  │                     │ │ _agents             │ │                  │  │ │
│  │  └─────────────────────┘ └─────────────────────┘ └────────┬─────────┘  │ │
│  └───────────────────────────────────────────────────────────┼────────────┘ │
└──────────────────────────────────────────────────────────────┼──────────────┘
                                                               │
                                                               │ HTTP/JSON-RPC
                                                               │ A2A Protocol
                                                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             A2A SERVER                                       │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                        A2AServer                                        │ │
│  │  ┌──────────────────┐  ┌───────────────────────┐  ┌─────────────────┐  │ │
│  │  │ FastAPI/Starlette│  │ DefaultRequestHandler │  │ AgentCard       │  │ │
│  │  │     HTTP App     │→ │  (A2A Protocol)       │  │ /.well-known/   │  │ │
│  │  └──────────────────┘  └───────────┬───────────┘  └─────────────────┘  │ │
│  └────────────────────────────────────┼───────────────────────────────────┘ │
│                                       ▼                                      │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                     StrandsA2AExecutor                                  │ │
│  │                                                                         │ │
│  │  A2A Parts ──────────► Strands ContentBlocks ──────────► Strands Agent │ │
│  │  (TextPart,FilePart)   (text,image,video,doc)            stream_async()│ │
│  │                                                                         │ │
│  │  A2A Events ◄────────── Streaming Response ◄──────────── Agent Output  │ │
│  │  (TaskState,artifacts)  (TaskUpdater)                                   │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                       │                                      │
│  ┌────────────────────────────────────▼───────────────────────────────────┐ │
│  │                        Strands Agent                                    │ │
│  │                   (with tools, model, etc.)                             │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Communication Flow

```
1. Discovery Phase
   ┌──────────────┐                              ┌────────────────┐
   │ Orchestrator │  GET /.well-known/agent.json │   A2A Server   │
   │    Agent     │ ────────────────────────────►│                │
   │              │ ◄──────────────────────────── │                │
   │              │     { AgentCard JSON }        │                │
   └──────────────┘                              └────────────────┘

2. Message Phase
   ┌──────────────┐                              ┌────────────────┐
   │ Orchestrator │  POST / (JSON-RPC)           │   A2A Server   │
   │    Agent     │ ────────────────────────────►│                │
   │              │  {"method":"message/send",   │                │
   │              │   "params":{"message":{...}}}│                │
   │              │                              │                │
   │              │ ◄──────────────────────────── │                │
   │              │  SSE or JSON response        │                │
   │              │  (Task + artifacts)          │                │
   └──────────────┘                              └────────────────┘
```

## Source Code Walkthrough

### 1. Server Side: A2AServer

**Location**: `src/strands/multiagent/a2a/server.py`

```python
class A2AServer:
    def __init__(self, agent: SAAgent, *, host="127.0.0.1", port=9000, ...):
        self.strands_agent = agent

        # Create the executor that bridges A2A ↔ Strands
        self.request_handler = DefaultRequestHandler(
            agent_executor=StrandsA2AExecutor(self.strands_agent),  # Key bridge
            task_store=task_store or InMemoryTaskStore(),
        )

    @property
    def public_agent_card(self) -> AgentCard:
        """Returns metadata for agent discovery"""
        return AgentCard(
            name=self.name,
            description=self.description,
            url=self.http_url,
            skills=self.agent_skills,  # Auto-derived from agent tools
            capabilities=AgentCapabilities(streaming=True),
        )
```

### 2. Server Side: StrandsA2AExecutor

**Location**: `src/strands/multiagent/a2a/executor.py`

```python
class StrandsA2AExecutor(AgentExecutor):
    async def execute(self, context: RequestContext, event_queue: EventQueue):
        task = new_task(context.message)
        updater = TaskUpdater(event_queue, task.id, task.context_id)
        await self._execute_streaming(context, updater)

    async def _execute_streaming(self, context, updater):
        # Convert A2A message parts → Strands ContentBlocks
        content_blocks = self._convert_a2a_parts_to_content_blocks(
            context.message.parts
        )

        # Execute the Strands agent with streaming
        async for event in self.agent.stream_async(content_blocks):
            await self._handle_streaming_event(event, updater)

    def _convert_a2a_parts_to_content_blocks(self, parts):
        """A2A → Strands format conversion"""
        for part in parts:
            if isinstance(part.root, TextPart):
                yield ContentBlock(text=part.root.text)
            elif isinstance(part.root, FilePart):
                # Decode base64, detect type, create ImageContent/VideoContent/etc.
                ...
```

### 3. Client Side: A2AClientToolProvider

**Location**: `strands-tools/src/strands_tools/a2a_client.py`

```python
class A2AClientToolProvider:
    def __init__(self, known_agent_urls=None, timeout=300, ...):
        self._known_agent_urls = known_agent_urls or []
        self._discovered_agents: dict[str, AgentCard] = {}

    @tool
    async def a2a_discover_agent(self, url: str) -> dict:
        """Fetch AgentCard from /.well-known/agent.json"""
        resolver = A2ACardResolver(httpx_client, base_url=url)
        agent_card = await resolver.get_agent_card()
        self._discovered_agents[url] = agent_card
        return {"status": "success", "agent_card": agent_card}

    @tool
    async def a2a_send_message(self, message_text: str, target_agent_url: str):
        """Send message using A2A protocol"""
        agent_card = await self._discover_agent_card(target_agent_url)
        client = self._get_client_factory().create(agent_card)

        message = Message(
            role=Role.user,
            parts=[Part(TextPart(text=message_text))],
        )

        async for event in client.send_message(message):
            return {"status": "success", "response": event}
```

## Data Conversion: A2A ↔ Strands

| A2A Part | Strands ContentBlock |
|----------|---------------------|
| `TextPart(text="Hello")` | `ContentBlock(text="Hello")` |
| `FilePart(image/png, bytes)` | `ContentBlock(image=ImageContent(format="png", source=...))` |
| `FilePart(video/mp4, bytes)` | `ContentBlock(video=VideoContent(format="mp4", source=...))` |
| `FilePart(application/pdf)` | `ContentBlock(document=DocumentContent(format="pdf", ...))` |
| `DataPart(data={"k":"v"})` | `ContentBlock(text="[Structured Data]\n{...}")` |
| `FilePart(uri="s3://...")` | `ContentBlock(text="[File: name] - Referenced at: uri")` |

## Complete Working Example

### Server (agent_server.py)

```python
from strands import Agent
from strands.multiagent.a2a import A2AServer
from strands_tools.calculator import calculator

agent = Agent(
    name="Calculator Agent",
    description="Performs arithmetic operations",
    tools=[calculator],
)
server = A2AServer(agent, host="0.0.0.0", port=9000)
server.serve()  # Blocks, serves at http://localhost:9000
```

### Client (orchestrator.py)

```python
from strands import Agent
from strands_tools.a2a_client import A2AClientToolProvider

# Create client tool provider with known agents
provider = A2AClientToolProvider(
    known_agent_urls=["http://localhost:9000"]
)

# Create orchestrator with A2A client tools
orchestrator = Agent(tools=provider.tools)

# The orchestrator can now:
# 1. Discover agents: a2a_list_discovered_agents()
# 2. Send messages: a2a_send_message("what is 5+3?", "http://localhost:9000")
response = orchestrator("Ask the calculator agent to compute 101 * 11")
```

## A2A Protocol Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | POST | Send messages (JSON-RPC) |
| `/.well-known/agent.json` | GET | Agent discovery (AgentCard) |
| `/tasks/get` | POST | Get task status |
| `/tasks/cancel` | POST | Cancel a task |
| `/` | SSE | Streaming responses |

## Key Files

| Component | Location |
|-----------|----------|
| A2AServer | `src/strands/multiagent/a2a/server.py` |
| StrandsA2AExecutor | `src/strands/multiagent/a2a/executor.py` |
| A2AClientToolProvider | `strands-tools/src/strands_tools/a2a_client.py` |

## Limitations

- **No cancellation** - `cancel()` raises `UnsupportedOperationError`
- **URI files not fetched** - Files with URI become text references only
- **Experimental** - API may have breaking changes

## See Also

- [A2A Protocol Documentation](https://a2aproject.github.io/A2A/latest/)
- [Strands A2A Samples](https://github.com/strands-agents/samples/tree/main/03-integrations/Native-A2A-Support)
