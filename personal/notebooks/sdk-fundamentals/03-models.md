# How Models Work in the Strands SDK

The model is the agent's brain. But in the SDK, "model" doesn't mean the AI itself -- it means the **adapter** that connects the SDK to the AI provider.

---

## The Translator Analogy

Amazon Bedrock, OpenAI, and Anthropic all speak different API languages. The SDK needs a common language.

The `Model` class is a **translator**. It translates between the SDK's language (Messages, ToolSpecs, StreamEvents) and each provider's native API:

```
SDK                  Model Adapter              AI Provider
                     (Translator)
Messages -------->   BedrockModel ----------->  Amazon Bedrock API
ToolSpecs ------->   (converts format)          (different format)
SystemPrompt ---->
                     <-----------
StreamEvents <----   (converts back)  <--------  Bedrock Response
```

Every model adapter does the same translation -- that's why you can swap providers without changing your agent code.

---

## The Model Abstract Base Class

**Source:** `src/strands/models/model.py`

```python
class Model(ABC):
    @abstractmethod
    async def stream(
        self,
        messages: Messages,
        tool_specs: list[ToolSpec],
        system_prompt: SystemPrompt,
        **kwargs,
    ) -> AsyncGenerator[StreamEvent, None]:
        """Stream response from the model."""
        ...

    def get_config(self) -> dict:
        """Return model configuration."""
        ...
```

### `stream()` -- the main method

Every model must implement this. It:
- **Takes in:** messages (conversation history), tool_specs (available tools), system_prompt (instructions)
- **Yields:** `StreamEvent` objects one at a time (streaming)

This is an abstract method -- you cannot call `Model().stream()` directly. You must use a specific implementation like `BedrockModel`.

### `get_config()` -- model settings

Returns a dictionary of the model's configuration:
```python
model = BedrockModel(model_id="us.anthropic.claude-sonnet-4-20250514", max_tokens=4096)
print(model.get_config())
# {"model_id": "us.anthropic.claude-sonnet-4-20250514", "max_tokens": 4096, ...}
```

---

## What are StreamEvents?

When the model generates a response, it doesn't send the entire response at once. It **streams** it in chunks. Each chunk is a `StreamEvent`.

Types of StreamEvents:
- **Content chunks:** Pieces of the response text, arriving one at a time
- **Tool use:** The model wants to call a tool
- **Stop reason:** Why the model stopped generating (`end_turn`, `tool_use`, `max_tokens`)
- **Usage stats:** Token counts (input tokens, output tokens)

This is why you see text appear word-by-word when an agent responds -- each word (approximately) is a separate StreamEvent.

---

## Available Model Providers

| Provider | Class | What it is | Install |
|----------|-------|-----------|---------|
| Amazon Bedrock | `BedrockModel` | **Default.** AWS managed service. Supports Claude, Amazon Nova, Llama, Mistral. | `pip install strands-agents` |
| Anthropic | `AnthropicModel` | Direct Anthropic API. Claude models. | `pip install strands-agents[anthropic]` |
| OpenAI | `OpenAIModel` | OpenAI API. GPT models. | `pip install strands-agents[openai]` |
| Google Gemini | `GeminiModel` | Google AI. Gemini models. | `pip install strands-agents[google]` |
| LiteLLM | `LiteLLMModel` | Universal adapter. 100+ providers through one interface. | `pip install strands-agents[litellm]` |
| Ollama | `OllamaModel` | Local models. Run AI on your own machine. | `pip install strands-agents[ollama]` |
| SageMaker | `SageMakerModel` | AWS SageMaker endpoints. Custom/fine-tuned models. | `pip install strands-agents` |

### Using each provider:

```python
from strands import Agent

# Amazon Bedrock (default -- no extra config needed)
from strands.models.bedrock import BedrockModel
agent = Agent(model=BedrockModel())

# Anthropic
from strands.models.anthropic import AnthropicModel
agent = Agent(model=AnthropicModel(model_id="claude-sonnet-4-20250514"))

# OpenAI
from strands.models.openai import OpenAIModel
agent = Agent(model=OpenAIModel(model_id="gpt-4o"))

# Local with Ollama
from strands.models.ollama import OllamaModel
agent = Agent(model=OllamaModel(model_id="llama3"))
```

---

## How Streaming Works

### With streaming (default):

```python
agent = Agent()  # Default callback_handler prints to console
result = agent("Tell me a joke")
# You see text appearing word-by-word in real-time:
# "Why did the..." (pause) "chicken cross..." (pause) "the road?"
```

The `callback_handler` receives each `StreamEvent` and prints it immediately. This is why you see text streaming in real-time.

### Without streaming:

```python
agent = Agent(callback_handler=None)
result = agent("Tell me a joke")
# Nothing appears until the entire response is ready.
# Then you access it:
print(result)  # "Why did the chicken cross the road? ..."
```

Setting `callback_handler=None` disables real-time output. The agent still works -- you just don't see the progress.

### Custom callback handler:

```python
def my_handler(event):
    # event contains the streaming chunk
    if hasattr(event, 'data'):
        print(f"[CHUNK] {event.data}", end="", flush=True)

agent = Agent(callback_handler=my_handler)
```

---

## How to Switch Models

The beauty of the SDK: same agent code, different models.

```python
from strands import Agent, tool

@tool
def get_weather(city: str) -> str:
    """Get the weather for a city."""
    return f"72F in {city}"

# Same agent, different brains:
from strands.models.bedrock import BedrockModel
agent_bedrock = Agent(model=BedrockModel(), tools=[get_weather])

from strands.models.openai import OpenAIModel
agent_openai = Agent(model=OpenAIModel(model_id="gpt-4o"), tools=[get_weather])

# Both work the same way:
result1 = agent_bedrock("Weather in Seattle?")
result2 = agent_openai("Weather in Seattle?")
```

What stays the same: tools, hooks, conversation management, message format.
What changes: the AI model that processes requests.

---

## Configuring the Default Model (BedrockModel)

```python
from strands.models.bedrock import BedrockModel

model = BedrockModel(
    model_id="us.anthropic.claude-sonnet-4-20250514",  # Which model to use
    max_tokens=4096,                                    # Max response length
    region_name="us-east-1",                            # AWS region
    # Additional params passed to the Bedrock API
)

agent = Agent(model=model)
```

Common model IDs for Amazon Bedrock:
- `us.anthropic.claude-sonnet-4-20250514` -- Claude Sonnet (balanced)
- `us.anthropic.claude-opus-4-20250514` -- Claude Opus (most capable)
- `us.anthropic.claude-haiku-3-5-20241022` -- Claude Haiku (fastest)
- `us.amazon.nova-pro-v1:0` -- Amazon Nova Pro

---

## Key Source Files

| File | What it does |
|------|-------------|
| `src/strands/models/model.py` | Model ABC -- `stream()`, `get_config()` |
| `src/strands/models/bedrock.py` | Amazon Bedrock adapter |
| `src/strands/models/anthropic.py` | Anthropic adapter |
| `src/strands/models/openai.py` | OpenAI adapter |
| `src/strands/types/streaming.py` | StreamEvent, StopReason types |
| `src/strands/event_loop/streaming.py` | `stream_messages()` utility |
