# Python Concepts You Need to Understand the Strands SDK

These concepts build on the basics covered in `../interrupt/00-python-basics-for-interrupts.md` (exceptions, dataclasses, protocols, TypedDicts, yield, setdefault). Read that first if you haven't.

---

## 1. What is `async`/`await`?

Normal Python code runs **one thing at a time**, in order. But some operations (like calling an AI model over the internet) take a long time. While waiting, your program does nothing.

**Async** lets your program do other work while waiting.

### Regular (synchronous) code:
```python
import time

def fetch_data():
    time.sleep(2)  # Simulates a slow network call -- program freezes for 2 seconds
    return "data"

result = fetch_data()  # Blocks here for 2 seconds
print(result)
```

### Async code:
```python
import asyncio

async def fetch_data():
    await asyncio.sleep(2)  # "Wait, but let other things run while I wait"
    return "data"

result = asyncio.run(fetch_data())
print(result)
```

Key vocabulary:
- **`async def`** -- defines a **coroutine** (a function that can pause and resume)
- **`await`** -- "pause here until this finishes, but let other things run meanwhile"
- **`asyncio`** -- Python's built-in library for running async code
- **Event loop** (Python's) -- the scheduler that decides which coroutine runs next

### `async for` -- iterating over async streams:
```python
async def stream_numbers():
    for i in range(3):
        await asyncio.sleep(0.1)
        yield i  # Produces values one at a time, asynchronously

async def main():
    async for number in stream_numbers():
        print(number)  # 0, 1, 2

asyncio.run(main())
```

### Why the SDK is async internally but sync externally

The SDK's event loop (`event_loop_cycle`) is an `async` generator -- it uses `await` to call the model and `yield` to stream events. But when you write `result = agent("hello")`, that's synchronous (no `async`/`await`).

The SDK bridges this gap with `run_async()` (`src/strands/_async.py`). It creates a new thread with its own asyncio event loop, runs the async code there, and returns the result to your synchronous code. You never need to write `async`/`await` yourself unless you want to.

```python
# You write this (synchronous):
result = agent("hello")

# Internally, the SDK does this:
# 1. Creates a new thread
# 2. Runs asyncio event loop in that thread
# 3. Calls agent.stream_async("hello") (which is async)
# 4. Returns the result to your synchronous code
```

**Why this matters for the SDK:** The entire event loop, model calls, and tool execution are async. Understanding `async`/`await` helps you read the SDK source code, especially `event_loop.py` and `agent.py`.

---

## 2. What is an Abstract Base Class (ABC)?

An **Abstract Base Class** is a class that says "I define the rules, but I can't be used directly. You must create a subclass that fills in the blanks."

```python
from abc import ABC, abstractmethod

class Animal(ABC):
    @abstractmethod
    def speak(self) -> str:
        """Every animal must implement this."""
        ...

    def breathe(self):
        """This is already implemented -- all animals breathe the same way."""
        return "inhale... exhale..."
```

You **cannot** create an `Animal` directly:
```python
a = Animal()  # TypeError: Can't instantiate abstract class Animal
```

You **must** create a subclass that implements the abstract methods:
```python
class Dog(Animal):
    def speak(self) -> str:
        return "Woof!"

class Cat(Animal):
    def speak(self) -> str:
        return "Meow!"

dog = Dog()
print(dog.speak())    # "Woof!"
print(dog.breathe())  # "inhale... exhale..."  (inherited from Animal)
```

**Why this matters for the SDK:** The `Model` class (`src/strands/models/model.py`) is an ABC. It defines `stream()` as an abstract method. Every model provider (BedrockModel, OpenAIModel, AnthropicModel) is a subclass that implements `stream()` differently. This is how the SDK supports multiple AI providers with the same interface.

```python
# You can't do this:
model = Model()  # Error!

# You must do this:
model = BedrockModel()   # OK -- implements stream()
model = OpenAIModel()    # OK -- implements stream()
```

---

## 3. What is a Decorator?

A **decorator** is a function that wraps another function to add behavior. The `@` symbol is shorthand for applying a decorator.

### Simple example:
```python
def shout(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return result.upper()
    return wrapper

@shout
def greet(name):
    return f"hello, {name}"

print(greet("alice"))  # "HELLO, ALICE"
```

What `@shout` does: it replaces `greet` with `wrapper`. When you call `greet("alice")`, you're actually calling `wrapper("alice")`, which calls the original `greet`, then uppercases the result.

Without the `@` syntax, the equivalent is:
```python
def greet(name):
    return f"hello, {name}"

greet = shout(greet)  # Same as @shout
```

### Decorators you'll see in the SDK:

**`@dataclass`** -- generates `__init__`, `__repr__`, `__eq__` methods:
```python
@dataclass
class Point:
    x: int
    y: int
```

**`@abstractmethod`** -- marks a method that subclasses must implement:
```python
class Model(ABC):
    @abstractmethod
    def stream(self):
        ...
```

**`@tool`** -- the SDK's decorator that transforms a function into an AgentTool:
```python
@tool
def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"72F in {city}"

# After @tool, get_weather is no longer a plain function.
# It's an AgentTool with: tool_name, tool_spec, tool_type, etc.
print(type(get_weather))  # <class 'DecoratorTool'>
print(get_weather.tool_name)  # "get_weather"
```

**Why this matters for the SDK:** The `@tool` decorator is how you create tools. It reads your function's name, docstring, and parameter types to automatically generate a JSON schema (tool_spec) that the AI model uses to understand what the tool does and how to call it. Understanding decorators helps you understand how `@tool` transforms your functions.

---

## 4. What is Inheritance vs Composition?

Two ways classes can relate to each other:

### Inheritance -- "is a" relationship
```python
class Model(ABC):
    @abstractmethod
    def stream(self):
        ...

class BedrockModel(Model):   # BedrockModel IS A Model
    def stream(self):
        # Amazon Bedrock-specific implementation
        ...

class OpenAIModel(Model):    # OpenAIModel IS A Model
    def stream(self):
        # OpenAI-specific implementation
        ...
```

`BedrockModel` **is a** `Model`. It inherits the interface and must implement abstract methods.

### Composition -- "has a" relationship
```python
class Agent:
    def __init__(self, model, tools, hooks):
        self.model = model   # Agent HAS A model
        self.tools = tools   # Agent HAS tools
        self.hooks = hooks   # Agent HAS hooks
```

`Agent` **has a** model. It doesn't inherit from Model -- it contains a Model instance as an attribute.

### When the SDK uses each:

| Pattern | Example | Why |
|---------|---------|-----|
| Inheritance | `BedrockModel(Model)` | All model providers must implement the same interface (`stream()`) |
| Inheritance | `SlidingWindowConversationManager(ConversationManager)` | All conversation managers must implement `apply_management()` |
| Composition | `Agent` has `self.model` | Agent uses a model but isn't a model |
| Composition | `Agent` has `self.tool_registry` | Agent uses tools but isn't a tool |

**Why this matters for the SDK:** Understanding when the SDK uses "is a" vs "has a" helps you navigate the codebase. Models and conversation managers use inheritance (you pick an implementation). Agent uses composition (you assemble an agent from parts).

---

## 5. What is `**kwargs`?

`**kwargs` collects **keyword arguments** into a dictionary.

```python
def greet(**kwargs):
    print(kwargs)

greet(name="Alice", age=30)
# Output: {'name': 'Alice', 'age': 30}
```

The reverse -- **unpacking** a dictionary into keyword arguments:
```python
data = {"city": "Seattle", "unit": "fahrenheit"}
get_weather(**data)
# Same as: get_weather(city="Seattle", unit="fahrenheit")
```

You can combine regular arguments with `**kwargs`:
```python
def func(required_arg, **kwargs):
    print(f"required: {required_arg}")
    print(f"extras: {kwargs}")

func("hello", x=1, y=2)
# required: hello
# extras: {'x': 1, 'y': 2}
```

**Why this matters for the SDK:**
- Tool functions receive their arguments as keyword arguments (the model sends `{"city": "Seattle"}`, the SDK calls `get_weather(city="Seattle")`)
- Hook callbacks use `**kwargs` for flexibility: `def register_hooks(self, registry, **kwargs)`
- Many SDK methods accept `**kwargs` to pass extra options through

---

## 6. What is a Lock?

A **Lock** prevents two things from running at the same time. It's like a bathroom door lock -- only one person can use it at a time.

```python
import threading

lock = threading.Lock()

def critical_operation():
    lock.acquire()    # "Lock the door"
    try:
        # Only one thread can be here at a time
        print("doing important work")
    finally:
        lock.release()  # "Unlock the door"
```

Shorter version using `with`:
```python
def critical_operation():
    with lock:  # Automatically acquires and releases
        print("doing important work")
```

**Why this matters for the SDK:** The Agent class has `self._invocation_lock` (`src/strands/agent/agent.py:245`). This prevents you from calling the same agent from two threads simultaneously, which would corrupt the conversation history. When you call `agent("hello")`, the lock is acquired at the start and released at the end. If another thread tries to call the agent while it's busy, it waits.

```python
# Thread 1:
result = agent("hello")  # Acquires lock, runs, releases lock

# Thread 2 (while Thread 1 is running):
result = agent("world")  # Waits for Thread 1 to finish, then runs
```

---

## 7. What is a Registry Pattern?

A **registry** is a dictionary that stores items by name, so you can look them up later.

```python
# Simple registry
registry = {}

def register(name, item):
    registry[name] = item

def get(name):
    return registry[name]

# Register items
register("calculator", calculator_tool)
register("weather", weather_tool)

# Look up by name
tool = get("calculator")
```

It's like a phone book -- you register entries by name and look them up later.

**Why this matters for the SDK:** Two key registries:

**ToolRegistry** (`src/strands/tools/registry.py`):
```python
# Stores tools by name
agent.tool_registry.registry = {
    "get_weather": <AgentTool>,
    "calculator": <AgentTool>,
}

# Methods:
agent.tool_registry.process_tools([get_weather, calculator])  # Register tools
agent.tool_registry.get_all_tool_specs()  # Get JSON schemas for model
```

**HookRegistry** (`src/strands/hooks/registry.py`):
```python
# Stores callbacks by event type
callbacks = {
    BeforeToolCallEvent: [callback1, callback2],
    AfterModelCallEvent: [callback3],
}
```

Both follow the same pattern: register by key, look up by key, iterate over values.

---

## Quick Reference Table

| Concept | One-liner | Used in SDK for... |
|---------|-----------|-------------------|
| async/await | Code that can pause and resume while waiting | Event loop, model calls, tool execution |
| ABC | Class that defines rules subclasses must follow | Model interface, ConversationManager interface |
| Decorator | Function that wraps another function | @tool transforms functions into AgentTools |
| Inheritance | "Is a" relationship (subclass) | BedrockModel is a Model |
| Composition | "Has a" relationship (attribute) | Agent has a Model |
| **kwargs | Collect/unpack keyword arguments | Tool argument passing, hook callbacks |
| Lock | Prevent concurrent access | Agent._invocation_lock |
| Registry | Dictionary of named items | ToolRegistry, HookRegistry |
