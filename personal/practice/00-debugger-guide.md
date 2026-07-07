# VS Code Debugger Guide for Beginners

A complete beginner's guide to using the VS Code debugger to step through Python code.

---

## 1. What is a Debugger?

A debugger lets you **pause your code at any line** and look around. Think of it like pausing a movie frame-by-frame:

- **Play** = your code runs normally
- **Pause** = your code freezes at a specific line
- **Frame forward** = you advance one line at a time
- **Look around** = you can see the value of every variable at that moment

Without a debugger, you add `print()` statements everywhere to see what's happening. With a debugger, you just pause and look.

---

## 2. Key Vocabulary

| Term | What it means |
|------|--------------|
| **Breakpoint** | A marker on a line that says "stop here." Code runs normally until it hits this line, then pauses. |
| **Step Over** (F10) | Run the current line and move to the next line. If the line calls a function, run the whole function without showing you the insides. |
| **Step Into** (F11) | If the current line calls a function, go INSIDE that function and pause at its first line. This is how you follow the code path. |
| **Step Out** (Shift+F11) | Finish the current function and go back to whoever called it. Useful when you've seen enough of a function. |
| **Continue** (F5) | Resume running at full speed until the next breakpoint (or the program ends). |
| **Call Stack** | The chain of "who called who." If `main()` called `foo()` which called `bar()`, the call stack shows: `bar` -> `foo` -> `main`. |
| **Variables Panel** | Shows all variables and their current values at the point where code is paused. |
| **Watch** | A list of expressions you want to monitor. You type them in, and VS Code shows their current values. |

---

## 3. How to Set a Breakpoint

1. Open a Python file in VS Code
2. Find the line where you want to pause
3. **Click in the gutter** -- that's the narrow area to the LEFT of the line numbers
4. A **red dot** appears -- that's your breakpoint
5. Click the red dot again to remove it

```
    Line numbers     Your code
    |                |
    v                v
    10               def my_function():
   *11                   x = 42          <-- Red dot on line 11 = breakpoint
    12                   y = x + 1
    13                   return y
```

You can set as many breakpoints as you want. The code will pause at each one.

---

## 4. How to Start the Debugger

1. Open the Python file you want to debug (e.g., `debug_agent.py`)
2. Make sure you have breakpoints set (red dots)
3. Press **F5** (or go to menu: **Run > Start Debugging**)
4. If VS Code asks "Select a debug configuration", pick **"Python File"**
5. Your code starts running. It runs at full speed until it hits the first breakpoint.
6. When it hits a breakpoint, **everything pauses**. You'll see:
   - The current line highlighted in yellow
   - The Variables panel on the left showing all variable values
   - The Debug toolbar at the top of the screen

---

## 5. The Debug Toolbar

When your code is paused, a toolbar appears at the top of VS Code:

```
  [ Continue ]  [ Step Over ]  [ Step Into ]  [ Step Out ]  [ Restart ]  [ Stop ]
       F5           F10            F11        Shift+F11   Ctrl+Shift+F5  Shift+F5
```

| Button | Keyboard | What it does |
|--------|----------|-------------|
| Continue | **F5** | Resume running until the next breakpoint |
| Step Over | **F10** | Execute the current line, move to the next line. Don't go inside function calls. |
| Step Into | **F11** | Go INSIDE the function being called on this line. This is the most important button for learning! |
| Step Out | **Shift+F11** | Finish the current function and return to the caller |
| Restart | **Ctrl+Shift+F5** | Stop and start debugging from the beginning |
| Stop | **Shift+F5** | Stop debugging entirely |

### The buttons you'll use most:

- **F11 (Step Into)** -- to follow the code path deeper
- **F10 (Step Over)** -- to skip over lines you don't care about
- **F5 (Continue)** -- to jump to the next breakpoint

---

## 6. The Debug Panels

When debugging, VS Code shows several panels on the left side:

### VARIABLES Panel

Shows all variables and their values at the current pause point.

```
VARIABLES
  Locals
    agent = <Agent object>
    result = "The weather is 72F"
    city = "Seattle"
  Globals
    ...
```

You can **expand objects** by clicking the arrow next to them. For example, clicking the arrow next to `agent` shows all its attributes:

```
  agent = <Agent object>
    > model = <BedrockModel>
    > messages = [...]
    > system_prompt = "You are a helpful..."
    > state = {}
```

### CALL STACK Panel

Shows which functions called which. The top of the stack is where you are now:

```
CALL STACK
  _handle_tool_execution    event_loop.py:450    <-- You are here
  event_loop_cycle          event_loop.py:180
  _run_loop                 agent.py:680
  stream_async              agent.py:620
  invoke_async              agent.py:410
```

Reading bottom to top: `invoke_async` called `stream_async` called `_run_loop` called `event_loop_cycle` called `_handle_tool_execution`. This is the call chain!

### DEBUG CONSOLE

A Python prompt at the bottom where you can type expressions:

```
> agent.messages
[{"role": "user", "content": [{"text": "What is 2+2?"}]}, ...]

> len(agent.messages)
2

> type(agent.model)
<class 'strands.models.bedrock.BedrockModel'>
```

Type any Python expression to inspect the current state. This is very powerful for understanding what variables contain at each step.

---

## 7. Step Into vs Step Over -- The Key Concept

This is the most important thing to understand:

### Example code:
```python
def add(a, b):      # Line 1
    result = a + b   # Line 2
    return result    # Line 3

x = add(2, 3)       # Line 5
print(x)             # Line 6
```

### If you're paused on Line 5 and press **Step Over (F10)**:
- Line 5 executes completely (calls `add`, gets result)
- You move to Line 6
- You never see Lines 1-3
- `x` is now `5`

### If you're paused on Line 5 and press **Step Into (F11)**:
- You jump INSIDE `add()` to Line 1
- Then F10/F11 to Line 2, Line 3
- Then you return to Line 5 (the call is done)
- Then Line 6

### For the Strands SDK:

When you're paused on `result = agent("hello")`:
- **Step Over (F10)**: Runs the entire agent call. You get the result but see nothing inside.
- **Step Into (F11)**: Takes you inside `Agent.__call__()` at `agent.py:335`. From there you can Step Into again to go deeper into `invoke_async`, then `stream_async`, etc.

**The path through the SDK:**
```
agent("hello")              <-- Step Into here
  -> __call__               <-- Step Into again
    -> invoke_async         <-- Step Into again
      -> stream_async       <-- Step Into again
        -> _run_loop        <-- Step Into again
          -> event_loop_cycle  <-- THE CORE ENGINE
```

At any point, press **Step Over (F10)** to skip a function you're not interested in, or **Step Out (Shift+F11)** to go back up one level.

---

## 8. Setting Breakpoints in Library Code (SDK Source Files)

You can set breakpoints not just in YOUR code, but also in the SDK source files.

### Method 1: Ctrl+Click (Cmd+Click on Mac)

1. In your code, hold **Ctrl** (or **Cmd** on Mac) and **click** on a class or function name
2. VS Code jumps to the source file where it's defined
3. Set breakpoints there just like your own code

Example:
- Ctrl+Click on `Agent` -> jumps to `src/strands/agent/agent.py`
- Ctrl+Click on `tool` -> jumps to `src/strands/tools/decorator.py`

### Method 2: Open the file directly

1. Press **Ctrl+P** (Quick Open)
2. Type `agent.py` or `event_loop.py`
3. Open the file from `src/strands/`
4. Set breakpoints on the lines you want

### Recommended SDK breakpoints

See `debug_agent.py` for the exact line numbers. The key locations are:

| File | Line | Function | What happens here |
|------|------|----------|------------------|
| `agent.py` | 335 | `__call__` | Entry point -- where `agent("hello")` starts |
| `agent.py` | 643 | `_run_loop` | Hooks fire, your message is appended |
| `event_loop.py` | 78 | `event_loop_cycle` | The core engine starts |
| `event_loop.py` | 275 | `_handle_model_execution` | The AI model is called |
| `event_loop.py` | 421 | `_handle_tool_execution` | Your tools are executed |
| `event_loop.py` | 236 | `recurse_event_loop` | Loops back for another cycle |
| `decorator.py` | 554 | `stream` | Your @tool function actually runs |

---

## Quick Reference

| Action | Keyboard | When to use |
|--------|----------|------------|
| Set breakpoint | Click in gutter | Before debugging, mark where to pause |
| Start debugging | **F5** | Begin! |
| Step Over | **F10** | Skip this line (don't go inside functions) |
| Step Into | **F11** | Go inside the function on this line |
| Step Out | **Shift+F11** | Leave this function, go back to caller |
| Continue | **F5** | Run until next breakpoint |
| Stop | **Shift+F5** | Done debugging |
| Inspect variable | Hover or Debug Console | See what a variable contains |
