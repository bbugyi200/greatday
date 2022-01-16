### State Diagram for the `greatday start` Command

The following diagram is kicked off when a user runs the `greatday start`
command. We assume that it has been `N` days since your tickler Todos were last
processed:

```mermaid
stateDiagram-v2
    state if_run_today <<choice>>
    state if_daily_check_failed <<choice>>

    ABC_priority: Process any Todos which have a priority of 'A', 'B', or 'C'.
    check_daily_todos: Run a series of tests against each Todo remaining in the daily file.
    collect: Collect Todos to add to daily file.
    collect_fuzzy: Prompt for Todos (using fuzzy matching) to add to daily file.
    collect_leftover: Collect any todos left over in daily file from last run.
    collect_priority_B: Collect any todos that have a priority greater than or equal to 'D'.
    create_backup_daily: Create a backup daily file.
    edit_daily: Open backup daily file in text editor.
    inbox: Process all Todos in your inbox (i.e. all Todos tagged with the @inbox context).
    prompt_for_save: ASK | Is it OK to commit the changes made to the daily file?
    remove_done_todos: Move any "done" Todos in the daily file to permenant storage.
    render_daily: Render the daily file after adding our newly collected Todos to it.
    save_daily_file: Commit the backup daily files contents to the real daily file.
    tickle: Process last N days of tickler Todos.
    verify_daily_todos: ASK | For verification / more information about Todo changes that we are unsure of.

    [*] --> ABC_priority
    ABC_priority --> tickle
    tickle --> if_run_today
    if_run_today --> collect: If this command was already run earlier today...
    if_run_today --> inbox
    inbox --> remove_done_todos: Else...
    remove_done_todos --> collect
    state collect {
        [*] --> collect_leftover
        collect_leftover --> collect_priority_B
        collect_priority_B --> collect_fuzzy
        collect_fuzzy --> [*]
    }
    collect --> render_daily
    render_daily --> create_backup_daily
    create_backup_daily --> edit_daily
    edit_daily --> check_daily_todos: When the user closes her text editor...
    check_daily_todos --> if_daily_check_failed
    if_daily_check_failed --> verify_daily_todos: If any of our tests from the previous step failed...
    if_daily_check_failed --> prompt_for_save: Else...
    verify_daily_todos --> prompt_for_save
    prompt_for_save --> save_daily_file: Yes
    prompt_for_save --> [*]: No
    save_daily_file --> [*]
```
