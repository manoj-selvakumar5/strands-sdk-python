# Hooks System Documentation

The Strands SDK provides a powerful hooks system that allows developers to extend and customize agent behavior through event-driven callbacks. This document explains the hooks architecture and how to use hooks with both single agents and multi-agent systems.

## Overview

Hooks in Strands SDK are based on a typed event system that enables you to:
- Intercept and modify agent behavior at key points
- Add custom logging, monitoring, and telemetry
- Transform inputs and outputs
- Implement custom error handling and retry logic
- Coordinate behavior across multi-agent systems

## Core Hooks Architecture

### Typed Events System (#745, #755)
The hooks system is built on a strongly-typed event architecture:

```python
from strands import Agent
from strands.hooks import Hook, BeforeToolInvocationEvent, AfterToolInvocationEvent

def my_before_tool_hook(event: BeforeToolInvocationEvent):
    print(f"About to call tool: {event.tool_name}")
    # Optionally modify the tool input
    event.tool_input["modified"] = True

def my_after_tool_hook(event: AfterToolInvocationEvent):
    print(f"Tool {event.tool_name} completed with result: {event.tool_result}")

agent = Agent(
    hooks=[
        Hook(BeforeToolInvocationEvent, my_before_tool_hook),
        Hook(AfterToolInvocationEvent, my_after_tool_hook)
    ]
)
```

## Available Hook Types

### 1. Tool Execution Hooks (#352)
Control and monitor tool calls:

- **BeforeToolInvocationEvent**: Fired before a tool is called
  - Can modify tool inputs
  - Can prevent tool execution
  - Access to tool name and parameters

- **AfterToolInvocationEvent**: Fired after tool execution
  - Access to tool results
  - Can modify tool outputs
  - Handle tool errors

```python
from strands.hooks import Hook, BeforeToolInvocationEvent

def validate_tool_input(event: BeforeToolInvocationEvent):
    if event.tool_name == "sensitive_operation":
        if not event.tool_input.get("authorized"):
            raise ValueError("Authorization required for sensitive operation")

agent = Agent(hooks=[Hook(BeforeToolInvocationEvent, validate_tool_input)])
```

### 2. Message Lifecycle Hooks (#385)
React to message events:

- **BeforeMessageAppendEvent**: Before messages are added to agent history
- **AfterMessageAppendEvent**: After messages are appended
- **MessageRedactionEvent**: When messages are redacted from sessions

```python
def log_new_messages(event: AfterMessageAppendEvent):
    print(f"New message added: {event.message.content[:50]}...")

agent = Agent(hooks=[Hook(AfterMessageAppendEvent, log_new_messages)])
```

### 3. Agent Lifecycle Hooks
Monitor agent initialization and execution:

- **AgentInitializedEvent**: When agent is first created
- **BeforeInvocationEvent**: Before agent processes input
- **AfterInvocationEvent**: After agent completes processing

```python
def track_agent_usage(event: BeforeInvocationEvent):
    # Custom telemetry tracking
    analytics.track("agent_invocation", {
        "agent_id": event.agent.id,
        "input_type": type(event.input).__name__
    })

agent = Agent(hooks=[Hook(BeforeInvocationEvent, track_agent_usage)])
```

## Value Modification with Hooks

Hooks can modify values during execution, enabling powerful transformations:

```python
def enhance_tool_input(event: BeforeToolInvocationEvent):
    """Add context and metadata to tool inputs"""
    if event.tool_name == "web_search":
        event.tool_input["context"] = "user_research_session"
        event.tool_input["timestamp"] = datetime.now().isoformat()

def format_tool_output(event: AfterToolInvocationEvent):
    """Transform tool outputs for consistency"""
    if isinstance(event.tool_result, dict):
        event.tool_result["processed_at"] = datetime.now().isoformat()
        event.tool_result["tool_version"] = "1.0"
```

## Hooks for MultiAgents (#760)

A major enhancement in August 2025 enabled hooks to work seamlessly with multi-agent orchestrators including Swarm and Graph patterns.

### MultiAgent Hook Capabilities

1. **Cross-Agent Coordination**: Hooks can coordinate behavior across multiple agents
2. **Shared State Management**: Use hooks to maintain shared state between agents
3. **Inter-Agent Communication**: Enable agents to communicate through hook events
4. **Collective Telemetry**: Monitor and log multi-agent workflows

### Example: Swarm with Hooks

```python
from strands.multiagent import Swarm
from strands.hooks import Hook, BeforeInvocationEvent
from strands import Agent

# Shared state for coordination
agent_activity = {}

def track_swarm_activity(event: BeforeInvocationEvent):
    agent_id = event.agent.id
    agent_activity[agent_id] = {
        "last_active": datetime.now(),
        "invocation_count": agent_activity.get(agent_id, {}).get("invocation_count", 0) + 1
    }
    
    # Coordinate agent workload
    if agent_activity[agent_id]["invocation_count"] > 10:
        print(f"Agent {agent_id} is handling heavy load - consider load balancing")

# Create agents with shared hooks
researcher = Agent(name="researcher", hooks=[Hook(BeforeInvocationEvent, track_swarm_activity)])
writer = Agent(name="writer", hooks=[Hook(BeforeInvocationEvent, track_swarm_activity)])
reviewer = Agent(name="reviewer", hooks=[Hook(BeforeInvocationEvent, track_swarm_activity)])

# Swarm with coordinated agents
swarm = Swarm(agents=[researcher, writer, reviewer])
```

### Example: Graph Orchestrator with Hooks

```python
from strands.multiagent import Graph
from strands.hooks import Hook, AfterToolInvocationEvent

def propagate_results(event: AfterToolInvocationEvent):
    """Share tool results across graph nodes"""
    # Store results in shared context
    graph_context = event.agent.context.get("graph_shared", {})
    graph_context[f"{event.agent.id}_{event.tool_name}"] = event.tool_result
    
    # Notify dependent agents
    if event.tool_name == "data_analysis":
        # Trigger downstream agents that depend on this analysis
        event.agent.context["trigger_downstream"] = True

# Create graph with interconnected agents
data_agent = Agent(name="data_processor", hooks=[Hook(AfterToolInvocationEvent, propagate_results)])
analysis_agent = Agent(name="analyzer", hooks=[Hook(AfterToolInvocationEvent, propagate_results)])
report_agent = Agent(name="reporter", hooks=[Hook(AfterToolInvocationEvent, propagate_results)])

graph = Graph()
graph.add_edge(data_agent, analysis_agent)
graph.add_edge(analysis_agent, report_agent)
```

## Advanced Hook Patterns

### 1. Conditional Hook Execution

```python
def conditional_logging(event: BeforeToolInvocationEvent):
    if os.getenv("DEBUG_TOOLS") == "true":
        logger.debug(f"Tool execution: {event.tool_name} with args {event.tool_input}")

agent = Agent(hooks=[Hook(BeforeToolInvocationEvent, conditional_logging)])
```

### 2. Hook Chaining and Ordering

```python
# Hooks execute in registration order
agent = Agent(hooks=[
    Hook(BeforeToolInvocationEvent, validate_input),      # First
    Hook(BeforeToolInvocationEvent, add_context),         # Second  
    Hook(BeforeToolInvocationEvent, log_execution),       # Third
])
```

### 3. Async Hook Support

```python
async def async_telemetry_hook(event: AfterToolInvocationEvent):
    await telemetry_client.track_tool_usage(
        tool=event.tool_name,
        duration=event.execution_time,
        success=event.success
    )

agent = Agent(hooks=[Hook(AfterToolInvocationEvent, async_telemetry_hook)])
```

## Session Integration

Hooks work seamlessly with session persistence (#302):

```python
def track_session_tools(event: AfterToolInvocationEvent):
    """Track tool usage per session"""
    session = event.agent.session
    if session:
        usage = session.metadata.get("tool_usage", {})
        usage[event.tool_name] = usage.get(event.tool_name, 0) + 1
        session.metadata["tool_usage"] = usage

agent = Agent(
    session_manager=FileSessionManager("./sessions"),
    hooks=[Hook(AfterToolInvocationEvent, track_session_tools)]
)
```

## Error Handling in Hooks

```python
def safe_hook_execution(event: BeforeToolInvocationEvent):
    try:
        # Your hook logic here
        risky_operation(event)
    except Exception as e:
        logger.error(f"Hook execution failed: {e}")
        # Don't break the agent execution
        pass

agent = Agent(hooks=[Hook(BeforeToolInvocationEvent, safe_hook_execution)])
```

## Best Practices

1. **Keep Hooks Lightweight**: Avoid blocking operations that could slow down agent execution
2. **Handle Errors Gracefully**: Don't let hook failures break agent workflows
3. **Use Async for I/O**: Use async hooks for database writes, API calls, etc.
4. **Validate Hook Inputs**: Check event properties before accessing them
5. **Document Hook Behavior**: Clearly document what your hooks do and any side effects
6. **Test Hook Integration**: Verify hooks work correctly with your agent workflows

## Related Features

- **Typed Events System** (#745, #755): Foundation for hooks architecture
- **Session Persistence** (#302): Hooks integrate with persistent sessions
- **Multi-Agent Orchestrators** (#416, #336): Swarm and Graph patterns with hook support
- **A2A Protocol**: Agent-to-agent communication enhanced by hooks
- **Telemetry Integration**: Built-in OpenTelemetry support works with hooks

The hooks system makes Strands SDK incredibly extensible, allowing you to customize every aspect of agent behavior while maintaining clean, maintainable code.