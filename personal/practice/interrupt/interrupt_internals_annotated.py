"""
================================================================================
 Strands Agents - Human-in-the-Loop INTERRUPTS - Annotated Internals Reference
================================================================================

NOTE: reference only - NOT meant to be executed or imported. It will not run
      (undefined runtime names, abridged bodies, and a deliberate metaclass mix).
      The SDK excerpts are LIVE Python (so your editor highlights them as code);
      only the explanations are `#` comments. Every excerpt carries the real
      source path + line numbers so you can open the actual file.

--------------------------------------------------------------------------------
WHAT THIS FILE IS
--------------------------------------------------------------------------------
A single, heavily-commented walkthrough of how an "interrupt" (a human-in-the-
loop pause/resume) works inside the Strands Python SDK. It stitches the ~10 files
involved into one narrative you can read top to bottom. Comments explain two
things at once:
    1. the interrupt MECHANISM, and
    2. the PYTHON IDIOMS used (dataclass, Protocol, setdefault, for/else,
       hasattr/getattr, generators/yield, dict subclassing, *-unpacking).

--------------------------------------------------------------------------------
THE ONE MENTAL MODEL: "RAISE AND REPLAY"
--------------------------------------------------------------------------------
An interrupt is NOT a suspended coroutine frozen in memory. Nothing is paused.

    PHASE 1 (TRIGGER):  the tool/hook runs, calls interrupt(), which RAISES a
                        Python exception. It unwinds everything and the agent
                        call returns with stop_reason="interrupt". Call is OVER.

    PHASE 2 (RESUME):   you call agent(...) again with the human's answer. The
                        tool/hook runs AGAIN from the top, but interrupt() now
                        RETURNS the answer instead of raising, and finishes.
                        stop_reason="end_turn".

So the tool body executes TWICE. The single line interrupt(...) is the pivot:
throws the first time, returns the second time. The only thing that "remembers"
the pause between the two calls is plain data on the agent
(agent._interrupt_state) - which is why interrupts can even be serialized and
resumed in another process later.

    Phase 1                              Phase 2
  agent("...")                        agent([responses])
      |                                    |
  tool/hook -> interrupt() RAISES      tool/hook -> interrupt() RETURNS "A"
      |                                    |
  loop unwinds, agent PARKS            tool/hook finishes, agent DEACTIVATES
      |                                    |
  stop_reason="interrupt"             stop_reason="end_turn"

--------------------------------------------------------------------------------
THE TWO TRIGGER PATHS (same outcome, different catch site)
--------------------------------------------------------------------------------
    Path A (HOOK): a BeforeToolCallEvent hook calls event.interrupt(...).
                   Exception caught in the HOOK REGISTRY.
    Path B (TOOL): the tool body calls tool_context.interrupt(...).
                   Exception caught in the @tool DECORATOR.
Both converge on the same internal event: ToolInterruptEvent.

--------------------------------------------------------------------------------
THE TWO "EVENT" SYSTEMS (do not confuse them)
--------------------------------------------------------------------------------
    * Hook LIFECYCLE events  -> base class HookEvent. The objects your callbacks
      receive. BeforeToolCallEvent ALSO mixes in _Interruptible, which is what
      gives it the .interrupt() method.
    * TypedEvents            -> base class TypedEvent(dict). Internal streaming
      events the loop yields (ToolInterruptEvent, EventLoopStopEvent). They are
      literally dicts, which is why you see event["stop"] access.
================================================================================
"""

from __future__ import annotations  # makes all annotations lazy strings, so the
#                                     type names below never need to exist at runtime.

import asyncio
import inspect
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Protocol, Sequence, TypedDict


# =============================================================================
# PLACEHOLDER STUBS  (NOT part of the SDK)
# =============================================================================
# Minimal stand-ins so the REAL excerpts below can be live, highlighted Python
# instead of comments. Everything in the numbered sections is faithful SDK code;
# only these few names are invented, purely to give the excerpts something to
# resolve against. None of it is meant to run.

def override(fn):            # the SDK uses typing.override (3.12+); passthrough here
    return fn

class HookEvent:             # stub of strands/hooks/registry.py :: HookEvent base
    ...

class HookProvider:          # stub of the HookProvider interface
    ...

class AgentTool:             # stub of the strands tool base class
    ...

def _has_tool_use_in_latest_message(messages):  # stub of event_loop.py helper
    ...

def tool(*args, **kwargs):   # stub of @tool; supports both @tool and @tool(...)
    def wrap(fn):
        return fn
    if args and callable(args[0]) and not kwargs:
        return args[0]       # bare @tool usage
    return wrap              # @tool(...) factory usage

class Agent:                 # stub of strands Agent
    def __init__(self, **kwargs):
        ...
    def __call__(self, prompt):
        ...


# =============================================================================
# SECTION 0 - THE TWO CONCRETE EXAMPLES WE TRACE
# =============================================================================
# The user-facing programs. Everything after this is the machinery that makes
# THESE behave the way they do. (The two agent(...) invocations are left as
# comments so nothing looks like it executes on import.)


# ------ Example B-path: the TOOL BODY raises the interrupt --------------------
# Style from: personal/practice/interrupt/debug_interrupt_tool.py
@tool(name="schedule_meeting", context=True)  # context=True -> Strands injects a
#                                               ToolContext as `tool_context`.
def schedule_meeting(tool_context, title: str, time: str) -> str:
    # This line runs TWICE across the two agent() calls:
    #   Phase 1: interrupt() RAISES  -> function abandoned here, never returns.
    #   Phase 2: interrupt() RETURNS -> `timezone` gets the human's answer.
    timezone = tool_context.interrupt(
        "timezone_selection",                                # the interrupt NAME
        reason=f"Which timezone for '{title}' at {time}?",   # human-readable why
    )
    # Everything below runs ONLY in Phase 2 (Phase 1 already raised above):
    print(f"SCHEDULING: '{title}' at {time} {timezone}")
    return f"Meeting '{title}' scheduled at {time} {timezone}"


# ------ Example A-path: a HOOK raises the interrupt BEFORE the tool runs ------
# Style from: the docstring example in strands/interrupt.py
@tool
def delete_tool(key: str) -> bool:
    print("DELETE_TOOL | deleting")
    return True


class ToolInterruptHook(HookProvider):
    def register_hooks(self, registry, **kwargs):
        # Register our callback against the BeforeToolCallEvent LIFECYCLE event.
        registry.add_callback(BeforeToolCallEvent, self.approve)

    def approve(self, event) -> None:
        # `event` is the data package Strands built for this tool call. It is
        # already in hand (Python passed it in as the argument) - we do not "find"
        # it. It carries .interrupt() via the _Interruptible mixin.
        if event.tool_use["name"] != "delete_tool":
            return
        # Phase 1: RAISES -> `approval` never assigned, approve() abandoned mid-line.
        # Phase 2: RETURNS "A" -> approval == "A", tool is NOT cancelled.
        approval = event.interrupt("for_delete_tool", reason="APPROVAL")
        if approval != "A":
            event.cancel_tool = "approval was not granted"


# agent = Agent(hooks=[ToolInterruptHook()], tools=[delete_tool], callback_handler=None)
#
# result = agent("delete object with key 'X'")   # PHASE 1
#   -> result.stop_reason == "interrupt";  result.interrupts == [Interrupt(...)]
#
# responses = [{"interruptResponse": {"interruptId": result.interrupts[0].id,
#                                      "response": "A"}}]
# result = agent(responses)                       # PHASE 2
#   -> result.stop_reason == "end_turn"


# =============================================================================
# SECTION 1 - CORE DATA STRUCTURES
# =============================================================================
# --- strands-py/src/strands/interrupt.py : lines 11-141 ---
# Three tiny types carry the whole feature: the payload (Interrupt), the control-
# flow signal (InterruptException), and the per-agent memory (_InterruptState).


# --- strands-py/src/strands/interrupt.py : lines 11-29 ---
@dataclass  # [interrupt.py:11] @dataclass auto-generates __init__/__repr__/__eq__
#                               from the fields below, so Interrupt(id, name, reason,
#                               response) works with no hand-written constructor.
class Interrupt:
    """Represents an interrupt that can pause agent execution for HITL workflows."""

    id: str            # [interrupt.py:22] deterministic unique key (see _interrupt_id).
    #                                       This is the DICT KEY the interrupt is stored
    #                                       under in Phase 1 and looked up by in Phase 2.
    name: str          # [interrupt.py:23] your label, e.g. "for_delete_tool".
    reason: Any = None # [interrupt.py:24] the "why", surfaced back to you on the result.
    response: Any = None
    # [interrupt.py:25] THE key field. None until a human answers.
    #   - Phase 1: created as None  -> interrupt() RAISES (no answer yet).
    #   - Phase 2: resume() sets it -> interrupt() RETURNS this value.
    #   The `= None` default is literally where the "response is None" state comes
    #   from: nobody has written an answer into this field yet.

    def to_dict(self) -> dict[str, Any]:  # [interrupt.py:27] used by session managers
        """Serialize to dict for session management."""
        return asdict(self)               # [interrupt.py:29] asdict() -> plain dict,
        #                                   JSON-serializable, for cross-process persistence.


# --- strands-py/src/strands/interrupt.py : lines 32-37 ---
class InterruptException(Exception):  # [interrupt.py:32] a NORMAL exception used
    #                                   deliberately as a control-flow SIGNAL (not
    #                                   because anything went wrong). `raise` is simply
    #                                   the cleanest way to stop everything and unwind
    #                                   the stack back out to the caller.
    """Exception raised when human input is required."""

    def __init__(self, interrupt: Interrupt) -> None:  # [interrupt.py:35]
        # Carries the Interrupt so whoever CATCHES it can pull it out
        # (via exception.interrupt) and turn it back into data.
        self.interrupt = interrupt  # [interrupt.py:37]


# --- strands-py/src/strands/interrupt.py : lines 40-141 (abridged) ---
@dataclass
class _InterruptState:  # [interrupt.py:41] the AGENT's interrupt memory. One per agent,
    #                     as agent._interrupt_state. It must survive BETWEEN the two
    #                     agent() calls - which is why it lives on the durable agent, not
    #                     on the throwaway event/context object.
    """Track the state of interrupt events raised by the user."""

    interrupts: dict[str, Interrupt] = field(default_factory=dict)
    # [interrupt.py:52] the id -> Interrupt map. Phase 1 inserts here; Phase 2 looks up
    #   here. field(default_factory=dict) gives each instance a FRESH empty dict (writing
    #   `= {}` would share ONE dict across all instances - the classic mutable-default bug).
    context: dict[str, Any] = field(default_factory=dict)
    # [interrupt.py:53] replay stash: the model's tool-use message + already-finished
    #   sibling tool results, so resume doesn't re-call the model or re-run finished tools.
    activated: bool = False
    # [interrupt.py:54] the switch. False = normal. True = "parked, waiting for a human".
    _version: int = field(default=0, compare=False, repr=False)
    # [interrupt.py:55] change-detection bookkeeping; ignore for the interrupt story.

    def activate(self) -> None:      # [interrupt.py:57] called when PARKING (Phase 1 end)
        self.activated = True        # [interrupt.py:59]
        self._version += 1

    def deactivate(self) -> None:    # [interrupt.py:62] called when the tool finally
        #                             completes on resume (Phase 2). Clears everything.
        self.interrupts = {}         # [interrupt.py:67]
        self.context = {}            # [interrupt.py:68]
        self.activated = False       # [interrupt.py:69]
        self._version += 1

    def resume(self, prompt) -> None:  # [interrupt.py:72]
        # Called at the VERY TOP of every agent() invocation (Section 9). This is what
        # writes the human's answer into the stored Interrupt BEFORE the loop re-runs
        # the tool/hook.
        if not self.activated:  # [interrupt.py:81] THE SELF-GUARD. On a fresh (non-resume)
            return              # [interrupt.py:82] call, activated is False -> do nothing.
            #                     This is why resume() can be called unconditionally at the
            #                     start of EVERY agent() call: it is a no-op unless parked.

        if not isinstance(prompt, list):  # [interrupt.py:84] on resume, prompt MUST be a
            #                               list of interruptResponse blocks, not a string.
            raise TypeError("must resume from interrupt with list of interruptResponse's")

        # [interrupt.py:87-93] (validation that every block is an "interruptResponse")
        # ... omitted for brevity ...

        contents = prompt  # [interrupt.py:95] (cast to list[InterruptResponseContent])
        for content in contents:                                          # [interrupt.py:96]
            interrupt_id = content["interruptResponse"]["interruptId"]    # [interrupt.py:97]
            interrupt_response = content["interruptResponse"]["response"] # [interrupt.py:98]
            if interrupt_id not in self.interrupts:  # [interrupt.py:100] the id you sent
                #                                      must match a stored one.
                raise KeyError(f"interrupt_id=<{interrupt_id}> | no interrupt found")
            self.interrupts[interrupt_id].response = interrupt_response
            # [interrupt.py:103] THE MUTATION. Reach into the Interrupt that Phase 1 stored
            #   (response was None) and overwrite response with the human answer. After
            #   this, interrupt() will see response != None and RETURN it.
        self.context["responses"] = contents  # [interrupt.py:105]

    def to_dict(self) -> dict[str, Any]:   # [interrupt.py:120] serialize whole state...
        return {                            # [interrupt.py:122]
            "interrupts": {k: v.to_dict() for k, v in self.interrupts.items()},
            "context": self.context,
            "activated": self.activated,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "_InterruptState":  # [interrupt.py:128]
        # ...and rebuild it. This to_dict/from_dict pair lets a SessionManager persist the
        # parked state after Phase 1 and reconstruct it before Phase 2 in a different
        # process. "Memory, not stack" is what makes durable resume possible.
        return cls(
            interrupts={
                interrupt_id: Interrupt(**interrupt_data)
                for interrupt_id, interrupt_data in data["interrupts"].items()
            },
            context=data["context"],
            activated=data["activated"],
        )


# =============================================================================
# SECTION 2 - THE HEART: _Interruptible.interrupt()
# =============================================================================
# --- strands-py/src/strands/types/interrupt.py : lines 79-123 ---
# This single method is the pivot of the whole system. Defined ONCE here, on the
# _Interruptible mixin, and INHERITED by both hosts that can raise an interrupt:
#     * ToolContext          (tool path) -> stores the agent as `.agent`
#     * BeforeToolCallEvent  (hook path) -> stores the agent as `.source`
# Writing it once and inheriting it is why the SAME code serves both paths - and
# why it must cope with the agent living under two different attribute names.


class _Interruptible(Protocol):  # [types/interrupt.py:79] Protocol = a CONTRACT /
    #                             interface. It declares what interruptible objects
    #                             provide, while also supplying this concrete interrupt()
    #                             body that subclasses reuse.
    """Interface that adds interrupt support to hook events and tools."""

    def interrupt(self, name: str, reason: Any = None, response: Any = None) -> Any:
        # [types/interrupt.py:82]
        #   self     = the object the method was CALLED ON. event.interrupt(...) passes
        #              `event` in as self - so we already HAVE the messenger; no lookup.
        #   name     = interrupt label (unique per hook callback).
        #   reason   = human-readable why.
        #   response = a PREEMPTIVE answer. Normally omitted (defaults to None). If you
        #              pass it, the interrupt never pauses - it returns immediately.
        #              This default None is one source of the "response is None" state.
        """Trigger the interrupt; returns the human response on resume, else raises."""

        # ---- Find the agent, coping with two possible attribute names ----------
        for attr_name in ["agent", "source"]:  # [types/interrupt.py:97] try these names in
            #                                     order: ToolContext uses `agent`, hook
            #                                     events use `source`.
            if hasattr(self, attr_name):        # [types/interrupt.py:98] hasattr(obj,"x")
                #                                 asks "does obj have attribute x?" (True/
                #                                 False) without risking an AttributeError.
                agent = getattr(self, attr_name)  # [types/interrupt.py:99] getattr(obj,"x")
                #                                   == obj.x, but the NAME is a string (needed
                #                                   because the name is a loop variable).
                break                             # [types/interrupt.py:100] stop at first
                #                                   match; `agent` wins over `source`.
        else:
            # [types/interrupt.py:101] FOR/ELSE: the else runs ONLY IF the loop finished
            #   WITHOUT `break`. So it fires only when NEITHER attribute existed - i.e.
            #   interrupt() was called on something that is neither a ToolContext nor a
            #   hook event. Fail loud rather than crash confusingly later.
            raise RuntimeError("agent instance attribute not set")  # [types/interrupt.py:102]

        id = self._interrupt_id(name)  # [types/interrupt.py:104] compute the DETERMINISTIC
        #   id. self._interrupt_id is polymorphic (tool vs hook differ), but for a given
        #   host+name it ALWAYS returns the same string. That determinism is what lets
        #   Phase 2 reconnect to the Phase 1 interrupt. (Definitions in Section 2b.)
        state = agent._interrupt_state  # [types/interrupt.py:105] the agent's durable
        #   interrupt memory. THIS is why we found the agent: the state we need lives on
        #   the agent (survives both calls), not on the throwaway self.

        interrupt_ = state.interrupts.setdefault(id, Interrupt(id, name, reason, response))
        # [types/interrupt.py:107] THE PIVOT LINE. dict.setdefault(key, default):
        #   - key present -> return the EXISTING value (ignore default).
        #   - key absent  -> INSERT default under key, return default.
        #   One line does insert-or-find:
        #     * Phase 1: id absent  -> inserts fresh Interrupt(response=None), returns it.
        #     * Phase 2: id present -> returns the STORED Interrupt (resume() set response).
        #   (trailing underscore just avoids clashing with the name "interrupt".)
        #   Subtle: in Phase 2 the Interrupt(...) default is still CONSTRUCTED (Python
        #   always evaluates arguments) but setdefault discards it, so the stored answer
        #   is never clobbered.

        if interrupt_.response is not None:  # [types/interrupt.py:108] the branch that
            #                                  makes one line behave two ways:
            return interrupt_.response       # [types/interrupt.py:109] Phase 2: answer
            #                                  present -> RETURN it; the tool/hook continues.

        raise InterruptException(interrupt_)  # [types/interrupt.py:111] Phase 1: no answer
        #   yet -> RAISE. Abandons the tool/hook mid-line and unwinds until a try/except
        #   catches it (Section 4 hooks, Section 5 tools).

    def _interrupt_id(self, name: str) -> str:  # [types/interrupt.py:113] the ABSTRACT
        #   declaration on the Protocol. Its body is just `...`: it defines the CONTRACT
        #   ("every interruptible produces a name -> str id") with no logic. The real
        #   logic lives in the subclasses (Section 2b). interrupt() calls
        #   self._interrupt_id, so the subclass version runs, never this empty one.
        """Unique id for the interrupt."""
        ...  # [types/interrupt.py:123] `...` (Ellipsis) = "no implementation here".


# =============================================================================
# SECTION 2b - THE TWO CONCRETE _interrupt_id IMPLEMENTATIONS
# =============================================================================
# Same method name, two different formulas, chosen by which object `self` is.
# Both deterministic (uuid5 is a HASH, not random) -> same inputs, same id, so the
# Phase-2 lookup matches the Phase-1 insert.


# --- strands-py/src/strands/types/tools.py : lines 131-162 ---
class ToolContext(_Interruptible):  # [tools.py:131] the object passed to context=True
    #                                 tools. Mixes in _Interruptible -> has .interrupt().
    tool_use: Any  # carries the model's toolUseId

    def _interrupt_id(self, name: str) -> str:  # [tools.py:153]
        return f"v1:tool_call:{self.tool_use['toolUseId']}:{uuid.uuid5(uuid.NAMESPACE_OID, name)}"
        # [tools.py:162]
        #   "v1:tool_call:"            -> version + category tag
        #   self.tool_use['toolUseId'] -> the model's id for THIS tool call
        #   uuid5(NAMESPACE_OID, name) -> stable hash of the interrupt name
        # Same toolUseId + same name => same id, every time.


# (BeforeToolCallEvent._interrupt_id is shown in Section 4, next to the event class.)


# =============================================================================
# SECTION 3 - THE RESUME RESPONSE SHAPES (what you pass back in Phase 2)
# =============================================================================
# --- strands-py/src/strands/types/interrupt.py : lines 126-145 ---
# TypedDict = a dict whose KEY NAMES and value types are declared for type-checking.
# At runtime it is just a plain dict. This is exactly what you build in Phase 2:
#   responses = [{"interruptResponse": {"interruptId": <id>, "response": "A"}}]


class InterruptResponse(TypedDict):  # [types/interrupt.py:126]
    """User response to an interrupt."""
    interruptId: str  # [types/interrupt.py:134] must equal result.interrupts[i].id
    response: Any     # [types/interrupt.py:135] the human's answer (any JSON-able value)


class InterruptResponseContent(TypedDict):  # [types/interrupt.py:138] the outer wrapper
    """Content block containing a user response to an interrupt."""
    interruptResponse: InterruptResponse  # [types/interrupt.py:145]
    #   the "interruptResponse" key is what resume() validates on and reads
    #   (interrupt.py:88, 97-98).


# =============================================================================
# SECTION 4 - TRIGGER PATH A: THE HOOK LIFECYCLE EVENT + THE REGISTRY CATCH
# =============================================================================


# --- strands-py/src/strands/hooks/events.py : lines 137-173 ---
@dataclass
class BeforeToolCallEvent(HookEvent, _Interruptible):  # [events.py:137] DOUBLE inheritance:
    #   HookEvent      -> a lifecycle event you can register callbacks on.
    #   _Interruptible -> grants the .interrupt() method.
    #   That combination is the whole reason event.interrupt(...) works.
    selected_tool: Any        # [events.py:155] the tool to invoke (hooks may swap it)
    tool_use: Any             # [events.py:156] the tool params (carries toolUseId)
    invocation_state: dict[str, Any]  # [events.py:157]
    cancel_tool: bool | str = False   # [events.py:158] set this to cancel the tool call

    @override
    def _interrupt_id(self, name: str) -> str:  # [events.py:164]
        return f"v1:before_tool_call:{self.tool_use['toolUseId']}:{uuid.uuid5(uuid.NAMESPACE_OID, name)}"
        # [events.py:173] NOTE the prefix is "v1:before_tool_call:" (vs "v1:tool_call:"
        #   for the tool path), so a hook interrupt and a tool-body interrupt get DISTINCT
        #   ids even for the same toolUseId+name. Determinism still holds within each path,
        #   which is all the resume matching needs.


# --- strands-py/src/strands/hooks/events.py : line 177 ---
@dataclass
class AfterToolCallEvent(HookEvent):  # [events.py:177] HookEvent ONLY - NO _Interruptible.
    #   Because it does not mix in _Interruptible, it has NO .interrupt() method: you
    #   cannot raise an interrupt AFTER the tool already ran. The constraint is expressed
    #   purely by which base classes the event inherits.
    result: Any


# --- strands-py/src/strands/hooks/registry.py : lines 301-345 (abridged) ---
# WHERE the Phase-1 InterruptException is caught on the hook path. Key idea: it is
# caught ONE LEVEL up (not "at the top"), and CONVERTED FROM EXCEPTION INTO DATA.
class HookRegistry:  # excerpt of strands/hooks/registry.py
    def get_callbacks_for(self, event):  # (stub) real code returns the registered callbacks
        ...

    async def invoke_callbacks_async(self, event):  # [registry.py:301]
        interrupts: dict[str, Interrupt] = {}       # [registry.py:326]
        for callback in self.get_callbacks_for(event):  # [registry.py:328]
            try:
                if inspect.iscoroutinefunction(callback):  # [registry.py:330]
                    await callback(event)
                else:
                    callback(event)  # [registry.py:333] YOUR approve() runs here; in
                    #                  Phase 1 it throws InterruptException.
            except InterruptException as exception:  # [registry.py:335] <-- CAUGHT HERE
                interrupt = exception.interrupt      # [registry.py:336] pull the Interrupt
                #                                      back out (exception -> data).
                if interrupt.name in interrupts:     # [registry.py:337] two callbacks used
                    #                                  the same name -> a real error.
                    raise ValueError("interrupt name used more than once")  # [registry.py:340]
                interrupts[interrupt.name] = interrupt  # [registry.py:343] collect as data.
        return event, list(interrupts.values())  # [registry.py:345] RETURN NORMALLY. The
        #   interrupt now rides a normal return value; from here up there is NO exception
        #   anymore - it flows as events.


# =============================================================================
# SECTION 5 - TRIGGER PATH B: THE @tool DECORATOR CATCH
# =============================================================================
# --- strands-py/src/strands/tools/decorator.py : lines 609-643 (abridged) ---
# When the interrupt comes from the TOOL BODY, the exception is caught here instead
# of the registry. Same idea: caught, converted to a ToolInterruptEvent.
class DecoratedFunctionTool:  # excerpt of strands/tools/decorator.py
    def _wrap_tool_result(self, tool_use_id, result):  # (stub) wraps a return value
        ...

    async def stream(self, tool_use, invocation_state, **kwargs):
        tool_use_id = tool_use.get("toolUseId", "unknown")  # [decorator.py:610]
        validated_input: dict[str, Any] = {}                # [decorator.py:611] (abridged)
        try:
            # ... (async-generator and coroutine branches, decorator.py:623-634, omitted) ...
            result = await asyncio.to_thread(self._tool_func, **validated_input)  # [decorator.py:638]
            #   ^ your sync tool runs on a worker thread; in Phase 1 it throws
            #     InterruptException out of this call.
            yield self._wrap_tool_result(tool_use_id, result)  # [decorator.py:639]
        except InterruptException as e:  # [decorator.py:641] <-- CAUGHT HERE
            yield ToolInterruptEvent(tool_use, [e.interrupt])  # [decorator.py:642] convert
            #   the caught exception into the SAME event the hook path produces.
            return  # [decorator.py:643]
    # So Path A (registry) and Path B (decorator) both end up yielding a
    # ToolInterruptEvent - the single hallway both entrances lead into.


# =============================================================================
# SECTION 6 - TRANSPORT EVENTS (TypedEvents)
# =============================================================================
# --- strands-py/src/strands/types/_events.py ---
# The INTERNAL streaming events (System B). TypedEvent IS a dict subclass - which is
# why every consumer accesses them with ["key"] syntax rather than .attribute.


class TypedEvent(dict):  # [_events.py:29] subclasses dict -> a TypedEvent literally IS a
    #                      dictionary with guaranteed keys. That is why you see
    #                      event["stop"] and tool_event["tool_interrupt_event"]["interrupts"].
    ...


class ToolInterruptEvent(TypedEvent):  # [_events.py:380]
    def __init__(self, tool_use, interrupts: list[Interrupt]) -> None:  # [_events.py:383]
        super().__init__(  # [_events.py:385] stores its payload under "tool_interrupt_event"
            {"tool_interrupt_event": {"tool_use": tool_use, "interrupts": interrupts}}
        )

    @property
    def interrupts(self) -> list[Interrupt]:  # [_events.py:392] convenience accessor
        return self["tool_interrupt_event"]["interrupts"]  # [_events.py:395]


class EventLoopStopEvent(TypedEvent):  # [_events.py:220]
    def __init__(self, stop_reason, message, metrics, request_state,  # [_events.py:223]
                 interrupts=None, structured_output=None, checkpoint=None):
        super().__init__(  # [_events.py:244]
            {"stop": (stop_reason, message, metrics, request_state,  # [_events.py:245]
                      interrupts, structured_output, checkpoint)}
        )
    # The final stop event. It packs a 7-TUPLE under "stop". Position 0 is the stop_reason
    # string ("interrupt", "end_turn", ...). Order matters because
    # AgentResult(*event["stop"]) unpacks it POSITIONALLY (Section 10).


# =============================================================================
# SECTION 7 - THE TOOL EXECUTOR
# =============================================================================
# --- strands-py/src/strands/tools/executors/_executor.py : lines 151-242 (abridged) ---
# The layer that (a) fires the before-tool hook and turns hook interrupts into a
# ToolInterruptEvent, and (b) streams the tool and registers interrupts into agent
# state so resume() can find them by id.
class ToolExecutor:  # excerpt of strands/tools/executors/_executor.py
    @staticmethod
    async def _invoke_before_tool_call_hook(agent, tool_func, tool_use, invocation_state):
        ...  # (stub) internally calls registry.invoke_callbacks_async, returns
        #      (event, list_of_interrupts)

    @staticmethod
    async def _execute(agent, tool_use, invocation_state, selected_tool, **kwargs):
        while True:  # [_executor.py:152] retry loop (hooks can request retries)
            before_event, interrupts = await ToolExecutor._invoke_before_tool_call_hook(
                agent, None, tool_use, invocation_state)  # [_executor.py:153] Path A
            #   interrupts arrive here as DATA (already converted by the registry).
            if interrupts:                                     # [_executor.py:157]
                yield ToolInterruptEvent(tool_use, interrupts)  # [_executor.py:158]
                return  # [_executor.py:159] tool is NOT run: on the hook path, delete_tool
                #         never executes in Phase 1.

            # ... (cancel_tool / unknown-tool handling, _executor.py:161-221, omitted) ...

            async for event in selected_tool.stream(tool_use, invocation_state, **kwargs):
                # [_executor.py:227]
                if isinstance(event, ToolInterruptEvent):  # [_executor.py:234] the tool-path
                    #                                        interrupt (from the decorator).
                    for interrupt in event.interrupts:     # [_executor.py:239]
                        agent._interrupt_state.interrupts.setdefault(interrupt.id, interrupt)
                        # [_executor.py:240] register the interrupt into agent state. For a
                        #   tool-context interrupt this is a no-op (interrupt() already
                        #   inserted it); it matters for sub-agent interrupts propagated in.
                    yield event  # [_executor.py:241]
                    return       # [_executor.py:242]
                # ... (ToolResultEvent / ToolStreamEvent handling omitted) ...


# =============================================================================
# SECTION 8 - THE EVENT LOOP (the four interrupt-relevant branches)
# =============================================================================
# --- strands-py/src/strands/event_loop/event_loop.py ---
# The event loop is a big async generator. Four spots read agent._interrupt_state to
# (Phase 1) park, and (Phase 2) take the resume shortcuts. Shown as focused excerpts.


# SHORTCUT 1 (Phase 2): skip the model entirely when parked.
async def _cycle_model_step(agent, invocation_state):  # excerpt: event_loop.py:282-289
    if agent._interrupt_state.activated:  # [event_loop.py:283]
        stop_reason = "tool_use"          # [event_loop.py:284]
        message = agent._interrupt_state.context["tool_use_message"]  # [event_loop.py:285]
        #   reuse the model's ORIGINAL Phase-1 tool-call decision instead of calling the
        #   model again. The model is not re-billed, and the SAME toolUseId comes back
        #   (so _interrupt_id matches).
    elif _has_tool_use_in_latest_message(agent.messages):  # [event_loop.py:287]
        ...
    else:
        ...  # normal path: actually call the model


# SHORTCUT 2 (Phase 2): re-run ONLY the interrupted tool.
async def _filter_tools(agent, tool_uses, tool_results):  # excerpt: event_loop.py:741-746
    if agent._interrupt_state.activated:  # [event_loop.py:741]
        tool_results.extend(agent._interrupt_state.context["tool_results"])  # [event_loop.py:742]
        #   re-inject results of sibling tools that already finished in Phase 1 (not re-run).
        tool_use_ids = {tr["toolUseId"] for tr in tool_results}  # [event_loop.py:745]
        tool_uses = [tu for tu in tool_uses if tu["toolUseId"] not in tool_use_ids]
        #   [event_loop.py:746] drop any tool that already has a result -> only the
        #   interrupted tool remains.


# PHASE 1: PARK. Where the agent parks after an interrupt bubbles up.
async def _park(agent, message, invocation_state, interrupts, tool_results,
                structured_output_result, cycle_start_time, cycle_trace):
    # excerpt: event_loop.py:807-825
    if interrupts:  # [event_loop.py:807]
        agent._interrupt_state.context = {"tool_use_message": message,  # [event_loop.py:809]
                                          "tool_results": tool_results}
        #   stash EVERYTHING needed to replay later (model decision + finished results).
        agent._interrupt_state.activate()  # [event_loop.py:810] flip activated = True.
        agent.event_loop_metrics.end_cycle(cycle_start_time, cycle_trace)  # [event_loop.py:812]
        yield EventLoopStopEvent(  # [event_loop.py:813]
            "interrupt",  # <-- the literal string that becomes result.stop_reason
            message,
            agent.event_loop_metrics,
            invocation_state["request_state"],
            interrupts,   # <-- becomes result.interrupts
            structured_output=structured_output_result,
        )
        return  # [event_loop.py:825] the loop STOPS; control returns out to agent(...).


# PHASE 2: DEACTIVATE. Reached when the replayed tool finished without a NEW interrupt.
async def _deactivate(agent):  # excerpt: event_loop.py:827
    agent._interrupt_state.deactivate()  # [event_loop.py:827] clears interrupts/context and
    #   sets activated=False. The loop then builds the toolResult message, recurses, the
    #   model IS called (activated now False), and produces the final answer -> "end_turn".


# =============================================================================
# SECTION 9 - THE AGENT INVOCATION (why resume() runs before the event loop)
# =============================================================================
# --- strands-py/src/strands/agent/agent.py : lines 1157-1201 (abridged) ---
# resume() applies your answer BEFORE the loop re-runs the tool simply because
# resume(prompt) is the FIRST statement of the invocation. No magic detection.
class _AgentInvocationExcerpt:  # excerpt of strands/agent/agent.py
    async def stream_async(self, prompt, invocation_state=None):
        try:
            self._interrupt_state.resume(prompt)  # [agent.py:1158] <-- FIRST thing.
            #   Always called, every invocation. Self-guards with `if not activated: return`,
            #   so no-op on fresh calls and only applies the answer on a real resume. MUST
            #   come first, so the stored Interrupt has response set BEFORE the loop re-runs
            #   the tool/hook and calls interrupt() again.
            self.event_loop_metrics.reset_usage_metrics()  # [agent.py:1160]
            # ... (checkpoint reset, state merge, agent.py:1162-1176, omitted) ...
            messages = await self._convert_prompt_to_messages(prompt)  # [agent.py:1183]
            # ... (the event loop is invoked further down) ...
        finally:
            ...

    def _build_result(self, event):
        result = AgentResult(*event["stop"])  # [agent.py:1201 / :1299]
        #   *event["stop"] SPREADS the 7-tuple positionally into AgentResult's fields.
        return result


# =============================================================================
# SECTION 10 - AgentResult (how stop_reason == "interrupt" falls out)
# =============================================================================
# --- strands-py/src/strands/agent/agent_result.py : lines 19-41 ---
# There is NO line that says result.stop_reason = "interrupt". It works purely by
# POSITION: "interrupt" is tuple element 0, and stop_reason is field 0.


@dataclass
class AgentResult:  # [agent_result.py:20]
    """Represents the last result of invoking an agent with a prompt."""

    stop_reason: Any           # [agent_result.py:35] <- gets tuple[0] == "interrupt"
    message: Any               # [agent_result.py:36] <- gets tuple[1]
    metrics: Any               # [agent_result.py:37] <- gets tuple[2]
    state: Any                 # [agent_result.py:38] <- gets tuple[3] (request_state)
    interrupts: Sequence[Interrupt] | None = None  # [agent_result.py:39] <- gets tuple[4]
    #   this is how result.interrupts gets populated - position 4 of the stop tuple.
    structured_output: Any = None  # [agent_result.py:40] <- gets tuple[5]
    checkpoint: Any = None         # [agent_result.py:41] <- gets tuple[6]
    #
    # Because AgentResult(*event["stop"]) unpacks positionally, and
    #   EventLoopStopEvent packs   (stop_reason, message, metrics, request_state,
    #                               interrupts, structured_output, checkpoint)
    #   AgentResult declares fields in the SAME order,
    # the "interrupt" string in slot 0 lands on stop_reason and the interrupt list in
    # slot 4 lands on interrupts. Three "firsts" (typed first at event_loop.py:813, first
    # tuple slot, first dataclass field) connect the string to the field.


# =============================================================================
# SECTION 11 - END-TO-END TIMELINES (tie every snippet together)
# =============================================================================
#
# ---- PHASE 1 (TRIGGER), hook path ------------------------------------------
#   agent("delete object X")
#     -> agent.py:1158  resume(prompt): activated is False -> NO-OP
#     -> event loop: model returns "call delete_tool" (toolUseId "tooluse_del789")
#     -> executor fires BeforeToolCallEvent -> your approve() runs
#         -> event.interrupt("for_delete_tool", reason="APPROVAL")   [types/interrupt.py:82]
#             -> _interrupt_id -> "v1:before_tool_call:tooluse_del789:<hash>"  [events.py:164]
#             -> setdefault INSERTS Interrupt(response=None)          [types/interrupt.py:107]
#             -> response is None -> RAISE InterruptException         [types/interrupt.py:111]
#         -> registry catches it, returns interrupt as DATA           [registry.py:335-345]
#     -> executor: if interrupts -> yield ToolInterruptEvent; return  [_executor.py:157-159]
#         (delete_tool NEVER runs)
#     -> event loop: if interrupts -> stash context + activate()      [event_loop.py:807-810]
#         -> yield EventLoopStopEvent("interrupt", ..., interrupts)   [event_loop.py:813]
#     -> AgentResult(*event["stop"])                                  [agent.py:1201]
#   RESULT: result.stop_reason == "interrupt", result.interrupts == [Interrupt(...)]
#   AGENT STATE: activated=True, interrupts={id: Interrupt(response=None)}, context={...}
#
# ---- PHASE 2 (RESUME), hook path -------------------------------------------
#   responses = [{"interruptResponse": {"interruptId": <same id>, "response": "A"}}]
#   agent(responses)
#     -> agent.py:1158  resume(prompt): activated is True ->
#         self.interrupts[id].response = "A"                          [interrupt.py:103]
#     -> event loop SHORTCUT 1: activated -> skip model, reuse stashed message
#         (same toolUseId comes back)                                 [event_loop.py:283-285]
#     -> event loop SHORTCUT 2: activated -> re-run only delete_tool  [event_loop.py:741-746]
#     -> executor fires BeforeToolCallEvent AGAIN -> approve() runs again
#         -> event.interrupt("for_delete_tool", ...)                  [types/interrupt.py:82]
#             -> _interrupt_id -> SAME id                             [events.py:164]
#             -> setdefault FINDS the stored Interrupt (response="A") [types/interrupt.py:107]
#             -> response is not None -> RETURN "A"                   [types/interrupt.py:109]
#         -> approval == "A" -> cancel_tool NOT set -> tool proceeds
#     -> delete_tool executes ("DELETE_TOOL | deleting", returns True)
#     -> no NEW interrupt -> deactivate()                             [event_loop.py:827]
#     -> build toolResult msg -> recurse -> model IS called -> final answer
#   RESULT: result.stop_reason == "end_turn"; agent state cleared (activated=False)
#
# ---- THE SYMMETRY IN ONE TABLE ---------------------------------------------
#   |            | setdefault (interrupt.py:107) | response       | branch taken       |
#   | Phase 1    | inserts fresh Interrupt       | None           | RAISE  -> park     |
#   | Phase 2    | finds stored Interrupt        | "A" (resume()) | RETURN -> continue |
#
#   Same interrupt() code path, same deterministic id, different stored response,
#   opposite outcome. `activated` is the switch that reshapes the LOOP around that
#   method so on resume the tool/hook reaches interrupt() in the identical position it
#   was in when it first raised. That alignment is the whole trick.
#
# ---- TOOL-PATH DIFFERENCES (Path B) ----------------------------------------
#   Everything is the same EXCEPT:
#     * the interrupt is raised from the tool body (tool_context.interrupt), not a hook;
#     * it is caught in the @tool decorator (decorator.py:641), not the registry;
#     * _interrupt_id uses prefix "v1:tool_call:" (tools.py:162), not "v1:before_tool_call:";
#     * on resume, the tool body itself replays (no before-hook to re-fire), and
#       interrupt() returns the answer at the exact line that previously raised.
# =============================================================================
