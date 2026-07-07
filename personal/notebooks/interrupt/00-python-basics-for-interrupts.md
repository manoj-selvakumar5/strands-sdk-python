# Python Basics You Need to Understand Interrupts

Before diving into the Strands SDK interrupt system, here are the Python concepts used in the code. Each section is self-contained with small examples.

---

## 1. What is an Exception?

An **exception** is Python's way of saying "something went wrong." When an error happens, Python **raises** an exception, which stops normal execution.

```python
# This raises a built-in exception
x = 1 / 0  # ZeroDivisionError: division by zero
```

You **catch** exceptions with `try/except`:

```python
try:
    x = 1 / 0
except ZeroDivisionError:
    print("Can't divide by zero!")
# Output: Can't divide by zero!
```

You can **create your own** exception classes:

```python
class MyError(Exception):
    pass

raise MyError("something bad happened")
```

You can also **attach data** to an exception:

```python
class MyError(Exception):
    def __init__(self, data):
        self.data = data

try:
    raise MyError({"key": "value"})
except MyError as e:
    print(e.data)  # {'key': 'value'}
```

**Why this matters for interrupts:** The SDK creates `InterruptException` — a custom exception that carries an `Interrupt` object. Raising it is how the SDK signals "stop, we need human input." Catching it is how the SDK collects the interrupt without crashing.

---

## 2. What is a Dataclass?

A **dataclass** is a shortcut for creating classes that mainly hold data. Instead of writing a full `__init__` method, Python generates it for you.

Without dataclass (verbose):
```python
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age
```

With dataclass (clean):
```python
from dataclasses import dataclass

@dataclass
class Person:
    name: str
    age: int
```

Both create objects the same way:
```python
p = Person("Alice", 30)
print(p.name)  # Alice
print(p.age)   # 30
```

Dataclasses also auto-generate `__repr__` (nice printing) and `__eq__` (comparison):
```python
print(p)  # Person(name='Alice', age=30)
```

You can set **default values**:
```python
@dataclass
class Person:
    name: str
    age: int
    email: str = "none"  # Default value
```

**Why this matters for interrupts:** The `Interrupt` class is a dataclass with four fields: `id`, `name`, `reason`, and `response`. The dataclass makes it easy to create, inspect, and serialize these objects.

---

## 3. What is a Protocol?

A **Protocol** defines "what methods an object must have" without requiring inheritance. It's Python's way of saying "if it walks like a duck and quacks like a duck, it's a duck."

```python
from typing import Protocol

class Drawable(Protocol):
    def draw(self) -> str:
        ...
```

Any class that has a `draw()` method satisfies this Protocol — it doesn't need to inherit from `Drawable`:

```python
class Circle:
    def draw(self) -> str:
        return "O"

class Square:
    def draw(self) -> str:
        return "[]"

def render(shape: Drawable):
    print(shape.draw())

render(Circle())  # Works! Circle has draw()
render(Square())  # Works! Square has draw()
```

**Why this matters for interrupts:** The SDK defines `_Interruptible` as a Protocol. Both `BeforeToolCallEvent` (a hook event) and `ToolContext` (used inside tools) implement this protocol. They both have an `interrupt()` method, so the same interrupt logic works in both places without code duplication.

---

## 4. What is a TypedDict?

A **TypedDict** is a dictionary with a fixed set of keys, each with a specified type. It's like a dataclass but for dictionaries.

```python
from typing import TypedDict

class UserResponse(TypedDict):
    userId: str
    answer: str
```

You create it like a normal dict:
```python
r: UserResponse = {"userId": "abc123", "answer": "yes"}
print(r["userId"])  # abc123
```

The difference from a regular dict: type checkers know exactly what keys exist and what types they have.

**Why this matters for interrupts:** The SDK uses `InterruptResponse` and `InterruptResponseContent` as TypedDicts. When you send back your response to an interrupt, you build a dictionary with specific keys (`interruptId`, `response`). TypedDicts document this expected structure.

---

## 5. What is `dict.setdefault()`?

`setdefault()` is a dict method that says: "get the value for this key; if it doesn't exist yet, insert this default and return it."

```python
d = {}

# Key "a" doesn't exist yet — insert "hello" and return it
val = d.setdefault("a", "hello")
print(val)  # "hello"
print(d)    # {"a": "hello"}

# Key "a" already exists — return existing value, DON'T overwrite
val = d.setdefault("a", "world")
print(val)  # "hello"  (not "world")
print(d)    # {"a": "hello"}  (unchanged)
```

**Why this matters for interrupts:** The `interrupt()` method uses `setdefault()` to store an `Interrupt` object. On the first call, it creates and stores the interrupt. On the second call (after resume), it finds the existing interrupt (which now has a response) and returns it. This one line powers the "dual-call" design:

```python
interrupt_ = state.interrupts.setdefault(id, Interrupt(id, name, reason, response))
```

---

## 6. What is `yield`?

`yield` turns a function into a **generator** — a function that produces values one at a time instead of all at once.

Regular function — returns everything at once:
```python
def get_numbers():
    return [1, 2, 3]

for n in get_numbers():
    print(n)
```

Generator function — produces values lazily:
```python
def get_numbers():
    yield 1
    yield 2
    yield 3

for n in get_numbers():
    print(n)
```

Both print `1, 2, 3`. The difference: the generator doesn't compute all values upfront. Each `yield` pauses the function and sends out one value. When you ask for the next value, the function resumes from where it paused.

A more practical example:
```python
def count_forever():
    n = 0
    while True:
        yield n
        n += 1

# Only generates values as you request them
for i in count_forever():
    print(i)
    if i >= 5:
        break
# Prints: 0, 1, 2, 3, 4, 5
```

**Async generators** use `async for` and `yield`:
```python
async def get_events():
    yield "event1"
    yield "event2"

async for event in get_events():
    print(event)
```

**Why this matters for interrupts:** The SDK's event loop is an async generator. It `yield`s events as they happen (model responses, tool calls, interrupts). When an interrupt occurs, the event loop yields a `ToolInterruptEvent` and then `return`s (stops generating), effectively pausing the entire agent.

---

## Quick Reference Table

| Concept | One-liner | Used in interrupt system for... |
|---------|-----------|-------------------------------|
| Exception | An error you can raise and catch | Stopping execution when human input needed |
| Dataclass | A class that holds data with less boilerplate | The `Interrupt` object (id, name, reason, response) |
| Protocol | An interface that says "must have these methods" | Sharing `interrupt()` between hooks and tools |
| TypedDict | A dictionary with typed, known keys | Structuring interrupt responses |
| `setdefault()` | Get-or-create for dictionaries | The dual-call trick (create on 1st call, retrieve on 2nd) |
| `yield` | Produce values one at a time | The event loop streaming events including interrupts |
