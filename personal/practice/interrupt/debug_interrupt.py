"""
debug_interrupt.py -- Step through the interrupt system with the VS Code debugger.

=============================================================================
HOW TO USE THIS FILE
=============================================================================

1. Open this file in VS Code.

2. IMPORTANT: Make sure "justMyCode" is OFF.
   A .vscode/launch.json has been created with the correct setting.
   To verify:
     - Open the Run and Debug sidebar: Ctrl+Shift+D (Cmd+Shift+D on Mac)
     - At the top, you should see "Debug Agent" in the dropdown
     - If you see "Python File" instead, click the dropdown and select "Debug Agent"

3. This file has TWO PHASES. You debug them in one run:
     Phase 1: The interrupt TRIGGERS (agent pauses)
     Phase 2: The interrupt RESUMES (agent continues)

4. Set breakpoints in SDK source files using the maps below.

5. Press F5 to start debugging.

6. Navigation reminder:
     F11         Step Into   -- go INSIDE the function on this line
     F10         Step Over   -- run this line, move to next
     Shift+F11   Step Out    -- finish this function, go back to caller
     F5          Continue    -- run until next breakpoint
     Shift+F5    Stop        -- quit debugging

=============================================================================
PHASE 1: TRIGGER -- The interrupt is raised (first agent call)
=============================================================================

Set breakpoints at these lines. They fire in this order when you call
agent("Delete the object with key 'my-file-123'"):

  File                                            Line   What happens
  ----                                            ----   ------------
  src/strands/agent/agent.py                      335    __call__()
     Entry point. agent("Delete...") starts here.

  src/strands/agent/agent.py                      595    self._interrupt_state.resume(prompt)
     Called but does nothing -- not activated yet.
     TIP: In Debug Console, type: self._interrupt_state.activated
     -> False

  src/strands/event_loop/event_loop.py            144    if agent._interrupt_state.activated:
     Check is False -> proceeds to call the model.
     TIP: In Debug Console, type: agent._interrupt_state.activated
     -> False

  src/strands/event_loop/event_loop.py            275    _handle_model_execution()
     The AI model is called. It responds: "I'll use delete_tool."

  src/strands/tools/executors/_executor.py        153    before_event, interrupts = await ...
     The BeforeToolCallEvent is about to fire.
     Your hook callback runs next.

  src/strands/types/interrupt.py                  107    interrupt_ = state.interrupts.setdefault(...)
     THE KEY LINE. Creates a new Interrupt object with response=None.
     TIP: Step Over (F10), then check: interrupt_.response
     -> None

  src/strands/types/interrupt.py                  111    raise InterruptException(interrupt_)
     Response is None -> RAISES the exception. Agent will pause.

  src/strands/hooks/registry.py                   238    except InterruptException as exception:
     The hook registry catches the exception. Does NOT crash.
     TIP: Check exception.interrupt.name
     -> "delete_approval"

  src/strands/tools/executors/_executor.py        157    if interrupts:
     Interrupts list is not empty -> yields ToolInterruptEvent.
     The tool itself NEVER runs.

  src/strands/event_loop/event_loop.py            485    if interrupts:
     Saves the current message and tool results into context.
     TIP: After F10, check: agent._interrupt_state.context.keys()

  src/strands/event_loop/event_loop.py            488    agent._interrupt_state.activate()
     Sets activated = True. The agent is now PAUSED.

  src/strands/event_loop/event_loop.py            491    yield EventLoopStopEvent("interrupt", ...)
     Returns "interrupt" as the stop_reason. Phase 1 done!


=============================================================================
PHASE 2: RESUME -- The agent continues (second agent call)
=============================================================================

Keep the SAME breakpoints. They fire again in this order when you call
agent(responses):

  src/strands/agent/agent.py                      335    __call__()
     Entry point again. agent(responses) starts here.

  src/strands/agent/agent.py                      595    self._interrupt_state.resume(prompt)
     THIS TIME IT DOES SOMETHING.
     TIP: Step Into (F11) to go inside resume().

  src/strands/interrupt.py                        100    self.interrupts[interrupt_id].response = interrupt_response
     Your "APPROVE" answer is written onto the Interrupt object.
     TIP: After F10, check: self.interrupts
     (the interrupt now has response="APPROVE")

  src/strands/event_loop/event_loop.py            144    if agent._interrupt_state.activated:
     Check is True -> SKIPS the model call completely.
     Uses the saved message from Phase 1 instead.
     TIP: In Debug Console, type: agent._interrupt_state.context.keys()
     -> dict_keys(['tool_use_message', 'tool_results', 'responses'])

  src/strands/event_loop/event_loop.py            460    if agent._interrupt_state.activated:
     True -> Restores partial tool results from Phase 1.
     Filters tool_uses to only the unresolved ones.

  src/strands/tools/executors/_executor.py        153    before_event, interrupts = await ...
     The hook fires AGAIN. Same callback runs.

  src/strands/types/interrupt.py                  107    interrupt_ = state.interrupts.setdefault(...)
     setdefault() finds the EXISTING Interrupt (does NOT create new).
     TIP: Step Over (F10), then check: interrupt_.response
     -> "APPROVE"  (it was filled in by resume!)

  src/strands/types/interrupt.py                  108    if interrupt_.response is not None:
     True! Returns "APPROVE" instead of raising the exception.
     THE AGENT CONTINUES.

  src/strands/tools/executors/_executor.py        157    if interrupts:
     Empty list this time -> tool proceeds normally.

  (Your delete_tool function runs here -- set a breakpoint inside it!)

  src/strands/event_loop/event_loop.py            505    agent._interrupt_state.deactivate()
     Clears all interrupt state. Back to normal.
     TIP: After F10, check: agent._interrupt_state.activated
     -> False

=============================================================================
THE CODE
=============================================================================
"""

from typing import Any

# Try: Ctrl+Click (or Cmd+Click) on "Agent" to jump to agent.py
from strands import Agent, tool

# Try: Ctrl+Click on these to jump to their source files
from strands.hooks import BeforeToolCallEvent, HookProvider, HookRegistry


# --- TOOL ---
# This tool only runs in Phase 2 (after the interrupt is approved).
@tool
def delete_tool(key: str) -> str:
    """Delete an object by its key.

    Args:
        key: The key of the object to delete.
    """
    # Set a breakpoint here to pause INSIDE your tool.
    # This line only executes in Phase 2 -- after approval.
    # In Phase 1, the interrupt stops execution BEFORE the tool runs.
    print(f"DELETING object with key: {key}")
    return f"Deleted object with key '{key}'"


# --- HOOK ---
# This hook runs BEFORE delete_tool. It asks for approval.
# It runs TWICE -- once in Phase 1 (raises), once in Phase 2 (returns).
class DeleteApprovalHook(HookProvider):
    """Hook that requires approval before deleting."""

    def register_hooks(self, registry: HookRegistry, **kwargs: Any) -> None:
        registry.add_callback(BeforeToolCallEvent, self.approve)

    def approve(self, event: BeforeToolCallEvent) -> None:
        # Only interrupt for delete_tool, not other tools
        if event.tool_use["name"] != "delete_tool":
            return

        # Set a breakpoint on the next line. It runs TWICE:
        #   Phase 1: event.interrupt() raises InterruptException
        #            (response is None, so it raises)
        #   Phase 2: event.interrupt() returns "APPROVE"
        #            (response was filled in by resume())
        approval = event.interrupt("delete_approval", reason="Approve deletion?")

        # This line ONLY runs in Phase 2.
        # In Phase 1, the exception was raised on the line above
        # and we never reach here.
        print(f"User responded with: {approval}")

        if approval != "APPROVE":
            event.cancel_tool = "Deletion was not approved by user."


# --- AGENT ---
agent = Agent(
    hooks=[DeleteApprovalHook()],
    tools=[delete_tool],
    system_prompt="You delete objects given their keys. Always use the delete_tool.",
    callback_handler=None,  # Disable streaming output for cleaner debugging
)

# ==========================================================================
# PHASE 1: TRIGGER THE INTERRUPT
# ==========================================================================
#
# Set a breakpoint on the next line, then:
#   - F5 to start debugging -> pauses here
#   - F11 (Step Into) to go inside agent.__call__()
#   - Follow the breakpoint map above
#
# Or set breakpoints in the SDK files and press F5 (Continue) to jump
# between them.

result = agent("Delete the object with key 'my-file-123'")

# After Phase 1, the agent has PAUSED. Inspect the result:
print("\n--- Phase 1 Complete ---")
print(f"stop_reason: {result.stop_reason}")            # "interrupt"
print(f"interrupts:  {len(result.interrupts)}")         # 1
print(f"name:        {result.interrupts[0].name}")      # "delete_approval"
print(f"reason:      {result.interrupts[0].reason}")    # "Approve deletion?"
print(f"response:    {result.interrupts[0].response}")  # None (not answered yet)

# ==========================================================================
# PHASE 2: RESUME WITH APPROVAL
# ==========================================================================
#
# Build the response. Each interrupt needs:
#   - interruptId: the ID from Phase 1
#   - response: your answer (any value -- here we use "APPROVE")

responses = [
    {
        "interruptResponse": {
            "interruptId": result.interrupts[0].id,
            "response": "APPROVE",
        }
    }
]

# Set a breakpoint on the next line for Phase 2.
# F11 (Step Into) to follow agent.__call__() again.

result = agent(responses)

# After Phase 2, the agent has COMPLETED. The tool ran.
print("\n--- Phase 2 Complete ---")
print(f"stop_reason: {result.stop_reason}")  # "end_turn"
print(f"response:    {result}")
print(f"messages:    {len(agent.messages)}")
