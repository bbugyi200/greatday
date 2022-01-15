### State Diagram for the `greatday start` Command

The following diagram is kicked off when a user runs the `greatday start`
command. We assume that it has been `N` days since your tickler Todos were last
processed:

```mermaid
stateDiagram-v2
    state if_run_today <<choice>>

    tickle: Process last N days of tickler Todos.
    inbox: Process all Todos in your inbox (i.e. all Todos tagged with the @inbox context).
    remove_done_todos: Move any "done" Todos in the daily file to permenant storage.
    collect: Collect Todos to add to daily file.
    edit_daily: Open daily file in text editor.
    check_daily: Ask for verification / more information about Todo changes that we are unsure of.
    render_daily: Render the daily file after adding our newly collected Todos to it.

    [*] --> if_run_today
    if_run_today --> tickle: Else...
    if_run_today --> collect: If this command was already run earlier today...
    tickle --> inbox
    inbox --> remove_done_todos
    remove_done_todos --> collect

    state collect {
        state if_leftover <<choice>>

        collect_leftover: Collect any todos left over in daily file from last run.
        collect_fuzzy: Prompt for Todos (using fuzzy matching) to add to daily file.

        [*] --> if_leftover
        if_leftover --> collect_leftover: If Todos are left in daily file from last run...
        if_leftover --> collect_fuzzy: Else...
        collect_leftover --> collect_fuzzy
        collect_fuzzy --> [*]
    }

    collect --> render_daily
    render_daily --> edit_daily
    edit_daily --> check_daily: When the user closes her text editor...
    check_daily --> [*]
```
