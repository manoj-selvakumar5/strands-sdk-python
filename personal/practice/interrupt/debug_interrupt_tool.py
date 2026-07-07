"""
debug_interrupt_tool.py -- Tool-based interrupt with the VS Code debugger.

=============================================================================
HOW THIS DIFFERS FROM debug_interrupt.py
=============================================================================

debug_interrupt.py uses a HOOK to trigger the interrupt:
  Hook fires BEFORE tool -> event.interrupt() -> InterruptException
  Caught at: hooks/registry.py:238

This file uses the TOOL ITSELF to trigger the interrupt:
  Tool starts running -> tool_context.interrupt() -> InterruptException
  Caught at: tools/decorator.py:609

Everything else (activate, resume, deactivate) is identical.

=============================================================================
HOW TO USE THIS FILE
=============================================================================

1. Open this file in VS Code.
2. Make sure "Debug Agent" is selected (needs justMyCode: false).
3. Set breakpoints from the map below.
4. Press F5 to start debugging.

=============================================================================
PHASE 1: TRIGGER -- The interrupt is raised (first agent call)
=============================================================================

Most breakpoints are the same as debug_interrupt.py. The DIFFERENT ones
are marked with *** below:

  File                                            Line   What happens
  ----                                            ----   ------------
  src/strands/agent/agent.py                      335    __call__()
  src/strands/agent/agent.py                      595    resume() no-op
  src/strands/event_loop/event_loop.py            144    activated check -> False
  src/strands/event_loop/event_loop.py            275    _handle_model_execution()

  *** THE PATH DIVERGES HERE ***

  src/strands/tools/executors/_executor.py        153    before_event, interrupts = ...
     No hook interrupt this time -> interrupts is empty.
     The tool starts executing.

  *** src/strands/tools/decorator.py              606    result = await asyncio.to_thread(self._tool_func, ...)
     Your tool function starts running.

  (inside your schedule_meeting function)
     tool_context.interrupt() is called.

  src/strands/types/interrupt.py                  107    setdefault() creates Interrupt
  src/strands/types/interrupt.py                  111    raise InterruptException

  *** src/strands/tools/decorator.py              609    except InterruptException as e:
     The DECORATOR catches it (not the hook registry).
     TIP: Check e.interrupt.name -> "timezone_selection"

  *** src/strands/tools/decorator.py              610    yield ToolInterruptEvent(...)
     Same event type, different origin.

  src/strands/event_loop/event_loop.py            485    if interrupts: saves context
  src/strands/event_loop/event_loop.py            488    activate()
  src/strands/event_loop/event_loop.py            491    yield "interrupt" stop

=============================================================================
PHASE 2: RESUME -- identical to debug_interrupt.py
=============================================================================

  src/strands/agent/agent.py                      335    __call__()
  src/strands/agent/agent.py                      595    resume() fills responses
  src/strands/interrupt.py                        100    sets response = "PST"
  src/strands/event_loop/event_loop.py            144    activated -> True, skips model
  src/strands/event_loop/event_loop.py            460    restores results, filters tools

  *** src/strands/tools/decorator.py              606    Tool runs AGAIN
  (inside your schedule_meeting function)
     tool_context.interrupt() returns "PST" this time.

  src/strands/types/interrupt.py                  107    setdefault() finds existing
  src/strands/types/interrupt.py                  108    response is not None -> returns "PST"

  (tool continues and finishes normally)

  src/strands/event_loop/event_loop.py            505    deactivate()

=============================================================================
THE CODE
=============================================================================
"""

from strands import Agent, tool
from strands.types.tools import ToolContext


@tool(name="schedule_meeting", context=True)
def schedule_meeting(tool_context: ToolContext, title: str, time: str) -> str:
    """Schedule a meeting with a title and time.

    Args:
        title: The title of the meeting.
        time: The time of the meeting.
    """
    # Set a breakpoint on the next line. It runs TWICE:
    #   Phase 1: tool_context.interrupt() raises InterruptException
    #            (the decorator catches it at decorator.py:609)
    #   Phase 2: tool_context.interrupt() returns "PST"
    #            (response was filled in by resume())
    timezone = tool_context.interrupt(
        "timezone_selection",
        reason=f"Which timezone for '{title}' at {time}?",
    )

    # This line ONLY runs in Phase 2.
    # In Phase 1, the exception was raised above.
    print(f"SCHEDULING: '{title}' at {time} {timezone}")
    return f"Meeting '{title}' scheduled at {time} {timezone}"


# --- AGENT ---
agent = Agent(
    tools=[schedule_meeting],
    system_prompt="You schedule meetings. Always use the schedule_meeting tool.",
    callback_handler=None,
)

# ==========================================================================
# PHASE 1: TRIGGER THE INTERRUPT
# ==========================================================================
# Set a breakpoint here, then F5 -> F11 (Step Into)

result = agent("Schedule a team standup at 9:00 AM")

print("\n--- Phase 1 Complete ---")
print(f"stop_reason: {result.stop_reason}")            # "interrupt"
print(f"interrupts:  {len(result.interrupts)}")         # 1
print(f"name:        {result.interrupts[0].name}")      # "timezone_selection"
print(f"reason:      {result.interrupts[0].reason}")    # "Which timezone for 'team standup' at 9:00 AM?"
print(f"response:    {result.interrupts[0].response}")  # None

# ==========================================================================
# PHASE 2: RESUME WITH RESPONSE
# ==========================================================================

responses = [
    {
        "interruptResponse": {
            "interruptId": result.interrupts[0].id,
            "response": "PST",
        }
    }
]

# Set a breakpoint here for Phase 2.

result = agent(responses)

print("\n--- Phase 2 Complete ---")
print(f"stop_reason: {result.stop_reason}")  # "end_turn"
print(f"response:    {result}")
print(f"messages:    {len(agent.messages)}")
