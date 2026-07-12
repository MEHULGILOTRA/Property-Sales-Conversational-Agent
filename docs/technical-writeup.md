# How I found and fixed a conversation-memory bug in a LangGraph agent

This project is a property-sales assistant built on LangGraph: a user states a budget and
city, the agent searches a SQLite database, shortlists the best matches, and books a site
visit. The pieces all looked right — a `MemorySaver` checkpointer, a state schema with
merge reducers, a FastAPI endpoint taking a `conversation_id`. But multi-turn
conversations over HTTP simply didn't work: the agent forgot the shortlist between
requests, and every property search ended with an out-of-place *"Which of the top
projects would you like to book?"*.

Here's what was actually wrong, and what fixing it taught me about LangGraph.

## Bug 1: a checkpointer nobody ever addressed

The graph was compiled correctly with memory:

```python
app = graph.compile(checkpointer=MemorySaver())
```

But the API handler invoked it like this:

```python
result = await self.graph.ainvoke(state)   # no config!
```

A LangGraph checkpointer is keyed by `thread_id`, passed at invoke time through
`config={"configurable": {"thread_id": ...}}`. Without it, the checkpointer never
loads or stores anything — the graph runs as if memory didn't exist. The
`conversation_id` from the request was even placed *into the state dict*, which feels
like it should matter, but LangGraph doesn't look there.

**Fix:** the conversation ID *is* the thread ID:

```python
config = {"configurable": {"thread_id": conversation_id}}
result = await graph.ainvoke({"messages": [...]}, config=config)
```

There were two accomplice bugs hiding behind this one:

1. **The service rebuilt the graph on every instance.** A fresh graph means a fresh
   `MemorySaver`, so even a correct `thread_id` would have found empty memory. The
   compiled graph must be a process-level singleton.
2. **The input dict wiped state on every turn.** The handler passed
   `{"messages": [...], "budget": None, "shortlisted_projects": []}` as input. Channels
   without a reducer take the *last write* — so the empty list overwrote the
   checkpointed shortlist on every request. The input should contain **only the new
   message**; everything else belongs to the checkpointer.

That last one is the subtle LangGraph lesson: *invoke input is a state update, not a
state template*. Anything you pass is applied as a write.

## Bug 2: the reply that was never read

Every node wrote its answer to `state["reply"]`, but the API returned:

```python
return result["messages"][-1]["content"]
```

Two problems in one line: the last message in `messages` is the *user's own message*
(nodes never appended AI messages), and it's a LangChain `HumanMessage` object, which
doesn't support `["content"]` subscripting. The CLI read `state["reply"]` correctly —
which is why the bug only bit over HTTP, and why "works on my machine" demos hid it.

## Bug 3: every search ended in a booking pitch

The graph wired the search pipeline like this:

```
extract_budget → sql_search → select_top → summarize → present → book_project → END
```

`book_project` ran unconditionally after every search, failed to fuzzy-match a project
name in a message that never asked to book anything, and overwrote the carefully built
search summary with *"Which of the top projects would you like to book?"*. The router
already had a booking-intent branch — the linear edge just bypassed it.

**Fix:** searches end at `present`. Booking is only reachable through the router when
the user expresses booking intent, with two continuation flags (`awaiting_email`,
`awaiting_project_choice`) so that mid-flow replies like a bare email address or a bare
project name route back into the booking node instead of triggering a new search.

## Bug 4: fuzzy matching booked the wrong project

With the flow fixed, a new bug surfaced in testing: *"I'd like to book a site visit"*
booked **Palm Vista**. Why?

```python
fuzz.partial_ratio("i'd like to book a site visit", "palm vista")  # → 62
```

`partial_ratio` finds the best-matching substring — and "site **visit**" vs "palm
**vista**" clears a 60 threshold. Switching to `token_set_ratio` drops the false match
to 36 while real project names still score 100. The end-to-end test that caught this is
now `test_project_choice_reply_continues_booking`.

## Takeaways

- **Memory bugs are configuration bugs.** The checkpointer, the thread ID, the graph
  singleton, and the invoke input all have to line up; any one of them silently
  disables memory while everything *looks* wired up.
- **Test over the same transport users take.** All four bugs were invisible from the
  CLI happy path and obvious from the first two HTTP calls.
- **Assert on the negative, too.** The regression test doesn't just check that search
  results appear — it checks the booking prompt *doesn't*.
