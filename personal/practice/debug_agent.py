"""
debug_agent.py -- Step through the Strands SDK with the VS Code debugger.

=============================================================================
HOW TO USE THIS FILE
=============================================================================

1. Open this file in VS Code.

2. IMPORTANT: Make sure "justMyCode" is OFF.
   Without this, the debugger REFUSES to step into SDK files!

   A .vscode/launch.json has been created with the correct setting.
   To verify:
     - Open the Run and Debug sidebar: Ctrl+Shift+D (Cmd+Shift+D on Mac)
     - At the top, you should see "Debug Agent" in the dropdown
     - If you see "Python File" instead, click the dropdown and select "Debug Agent"

   If .vscode/launch.json doesn't exist, create it with:
   {
       "version": "0.2.0",
       "configurations": [{
           "name": "Debug Agent",
           "type": "debugpy",
           "request": "launch",
           "program": "${file}",
           "justMyCode": false,
           "console": "integratedTerminal"
       }]
   }

3. Set breakpoints in SDK source files (see the map below).
   To navigate to SDK files:
     - Hold Ctrl (or Cmd on Mac) and click on "Agent" below -> jumps to agent.py
     - Hold Ctrl and click on "tool" below -> jumps to decorator.py
     - Or press Ctrl+P and type the filename (e.g., "event_loop.py")

4. Press F5 to start debugging.
   Make sure "Debug Agent" is selected in the debug dropdown (NOT "Python File").

5. The code will run until it hits your first breakpoint.

6. Use these keys to navigate:
     F11         Step Into   -- go INSIDE the function on this line
     F10         Step Over   -- run this line, move to next (skip insides)
     Shift+F11   Step Out    -- finish this function, go back to caller
     F5          Continue    -- run until next breakpoint
     Shift+F5    Stop        -- quit debugging

7. Look at the VARIABLES panel (left side) to see variable values.
   Look at the CALL STACK panel to see which function called which.
   Type expressions in the DEBUG CONSOLE (bottom) to inspect anything.

=============================================================================
RECOMMENDED BREAKPOINTS
=============================================================================

Set breakpoints at these lines in the SDK source files.
They fire in this order when you call agent("What is 2+2?"):

  File                                    Line   Function
  ----                                    ----   --------
  src/strands/agent/agent.py              335    __call__()
     The entry point. This is where agent("hello") starts.

  src/strands/agent/agent.py              376    invoke_async()
     Bridges sync to async. Calls stream_async().

  src/strands/agent/agent.py              539    stream_async()
     Acquires the lock. Converts your prompt to a message.

  src/strands/agent/agent.py              643    _run_loop()
     Fires BeforeInvocation hook. Appends your message to history.

  src/strands/event_loop/event_loop.py    78     event_loop_cycle()
     THE CORE ENGINE. This is where the magic happens.

  src/strands/event_loop/event_loop.py    275    _handle_model_execution()
     Calls the AI model. Streams the response.

  --- If the model wants to use a tool: ---

  src/strands/event_loop/event_loop.py    421    _handle_tool_execution()
     Extracts tool requests from the model's response.

  src/strands/tools/decorator.py          554    stream()
     Your @tool function actually executes here.

  src/strands/event_loop/event_loop.py    236    recurse_event_loop()
     Calls event_loop_cycle() again for the next cycle.

  --- Cycle 2: model sees tool results ---

  src/strands/event_loop/event_loop.py    275    _handle_model_execution()
     Model is called again. It now has the tool result.

  --- Model returns end_turn -> Done! ---

=============================================================================
THE CODE
=============================================================================
"""

# Try: Ctrl+Click (or Cmd+Click) on "Agent" to jump to agent.py
from strands import Agent

# Try: Ctrl+Click on "tool" to jump to decorator.py
from strands import tool


# Define a simple calculator tool.
# When the model decides to use this, execution goes through:
#   event_loop.py -> _handle_tool_execution -> decorator.py -> this function
@tool
def calculator(expression: str) -> str:
    """Perform a math calculation.

    Args:
        expression: A math expression like '2 + 2' or '15 * 7'.
    """
    # Set a breakpoint on the next line to pause INSIDE your tool.
    # When paused here, look at the VARIABLES panel to see:
    #   - expression: the string the model sent (e.g., "2 + 2")
    #   - The CALL STACK shows the full chain that got you here
    result = eval(expression)
    return str(result)


# Create the agent with our tool.
# Try: Ctrl+Click on "Agent" to open agent.py and set breakpoints there.
agent = Agent(
    tools=[calculator],
    callback_handler=None,  # Disable streaming output for cleaner debugging
)

# ==========================================================================
# THIS IS THE LINE TO DEBUG
# ==========================================================================
#
# Set a breakpoint on the next line, then:
#   - F5 to start debugging -> pauses here
#   - F11 (Step Into) to go inside agent.__call__()
#   - From there, keep pressing F11 to follow the entire call chain
#
# Or set breakpoints in the SDK files listed above and press F5 (Continue)
# to jump between them.

result = agent("What is 2 + 2?")

# After debugging, this prints the result.
print(f"\nResult: {result}")
print(f"Messages: {len(agent.messages)}")
