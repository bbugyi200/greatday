### State Diagram for the `greatday start` Command

The following diagram is kicked off when a user runs the `greatday start`
command. We assume that it has been `N` days since your tickler Todos were last
processed:

```mermaid
stateDiagram-v2
    tickle: Process last N days of tickler Todos.
    inbox: Process all Todos in your inbox (i.e. all Todos tagged with the @inbox context).
    collect: Collect Todos to add to daily (i.e. "today.txt") file.
    daily: Open daily file in text editor.
    check_daily: Ask for verification / more information about Todo changes that we are unsure of.
    prompt_if_done: Is the user done using `greatday`?

    [*] --> tickle
    tickle --> inbox
    inbox --> collect

    state collect {
        state if_leftover <<choice>>

        collect_leftover: Collect any todos left over in daily file from last run (verify user is OK with this).
        collect_ctx_prompt: Prompt for a list of contexts that we will collect Todos from.
        collect_fuzzy: For each context selected, prompt (using fuzzy matching) for Todos to add to daily file.

        [*] --> if_leftover
        if_leftover --> collect_leftover: If Todos are left in daily file from last run...
        if_leftover --> collect_ctx_prompt: Else...
        collect_leftover --> collect_ctx_prompt
        collect_ctx_prompt --> collect_fuzzy
        collect_fuzzy --> [*]
    }

    collect --> daily
    daily --> check_daily: When the user closes his/her text editor...
    check_daily --> prompt_if_done
    prompt_if_done --> [*]: Yes
    prompt_if_done --> collect: No
```
