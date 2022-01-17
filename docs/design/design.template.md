### State Diagram for the `greatday start` Command

The following diagram is kicked off when a user runs the `greatday start`
command. We assume that it has been `N` days since your tickler Todos were last
processed:

```mermaid
stateDiagram-v2
    state if_run_today <<choice>>
    state if_daily_check_failed <<choice>>
    state if_old_backup_file <<choice>>

    ABC_priority: Process any Todos which have a priority of 'A', 'B', or 'C'.
    ask_if_ok_to_save: ASK | Is it OK to commit the changes made to the daily file?
    ask_to_delete_backup: ASK | Can we delete the backup daily file?
    ask_to_verify_todos: ASK | For verification / more information about Todo changes that we are unsure of.
    check_daily_todos: Run a series of tests against each Todo remaining in the daily file.
    collect: Collect Todos to add to daily file.
    collect_fuzzy: Prompt for Todos (using fuzzy matching) to add to daily file.
    collect_leftover: Collect any todos left over in daily file from last run.
    collect_priority_B: Collect any todos that have a priority greater than or equal to 'D'.
    create_backup_daily: Create a backup daily file.
    edit_daily: Open backup daily file in text editor.
    inbox: Process all Todos in your inbox (i.e. all Todos tagged with the @inbox context).
    remove_done_todos: Move any "done" Todos in the daily file to permenant storage.
    render_daily: Render the daily file after adding our newly collected Todos to it.
    save_daily_file: Commit the backup daily file's contents to the real daily file.
    tickle: Process last N days of tickler Todos.

    [*] --> ABC_priority
    ABC_priority --> tickle
    tickle --> if_old_backup_file
    if_old_backup_file --> ask_to_delete_backup: IF | The backup daily file's contents differ from the daily file.
    if_old_backup_file --> if_run_today: ELSE
    ask_to_delete_backup --> if_run_today: YES
    ask_to_delete_backup --> edit_daily: NO
    if_run_today --> collect: IF | This command was already run earlier today.
    if_run_today --> inbox: ELSE
    inbox --> remove_done_todos
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
    if_daily_check_failed --> ask_to_verify_todos: IF | Any of our tests from the previous step failed.
    if_daily_check_failed --> ask_if_ok_to_save: ELSE
    ask_to_verify_todos --> ask_if_ok_to_save
    ask_if_ok_to_save --> save_daily_file: YES
    ask_if_ok_to_save --> [*]: NO
    save_daily_file --> [*]
```

### Class Diagrams

This section contains class diagrams used to help design / document greatday.

#### Class Diagram for `Todo` Classes

The following diagram illustrates how the various [magodo][1] `Todo` classes
interact.

Keep in mind the following notes while reviewing this diagram:

* The type variable `Self` is implicit and is always bound by the current class.
* The type variable `T` is bound by the `AbstractTodo` protocol.

```mermaid
classDiagram
    class AbstractTodo {
        <<protocol>>

        contexts : Iterable~str~
        create_date : Optional~date~
        desc : str
        done : bool
        done_date : Optional~date~
        metadata : dict~str, str~
        priority : Literal~A, B, ..., Z~
        projects : Iterable~str~

        from_line(cls, line: str)$ ErisResult~Self~
        new(**kwargs: Any) Self
        to_line() str
    }

    class Todo {
        <<concrete>>
    }

    class AbstractMagicTodo~T~ {
        <<protocol>>

        from_line_spells : Iterable~Callable[[str], str]~
        to_line_spells : Iterable~Callable[[str], str]~
        todo : T
        todo_spells : Iterable~Callable[[T], ErisResult[T]]~

        cast_from_line_spells(line: str)$ str
        cast_to_line_spells(line: str) str
        cast_todo_spells(todo: T)$ ErisResult~T~
    }

    class MagicTodoMixin~Todo~ {
        <<abstract>>
    }

    class ToInboxTodo~Todo~ {
        <<concrete>>
    }

    class FromInboxTodo~Todo~ {
        <<concrete>>
    }

    class ToDailyTodo~Todo~ {
        <<concrete>>
    }

    class FromDailyTodo~Todo~ {
        <<concrete>>
    }

    AbstractMagicTodo --|> AbstractTodo: inherits
    AbstractMagicTodo --* "1" AbstractTodo: contains
    Todo ..> AbstractTodo: implements
    MagicTodoMixin ..> AbstractMagicTodo: implements
    MagicTodoMixin --* "1" Todo: contains
    ToInboxTodo --|> MagicTodoMixin: inherits
    FromInboxTodo --|> MagicTodoMixin: inherits
    ToDailyTodo --|> MagicTodoMixin: inherits
    FromDailyTodo --|> MagicTodoMixin: inherits
```

#### Class Diagram for `Repo` and `UnitOfWork` Classes

The following diagram illustrates how the various [potoroo][2] `Repo` and `UnitOfWork`
(Unit-of-Work) classes interact.

Keep in mind the following notes while reviewing this diagram:

* `V_or_None` is meant to be `Optional[V]`. There seems to be a bug in
  [mermaid][3], however, that prevents us from using `Optional[V]` as a generic
  type.
* Similarly, `VList_or_None` is meant to be `Optional[List[V]]`.
* The type variable `Self` is implicit and is always bound by the current class.
* The type variable `T` is bound by the `AbstractTodo` protocol.
* The type variable `R` is bound by the `BasicRepo` class.
* The type variables `K`, `V`, and `Tag` are all unbound.

```mermaid
classDiagram
    class BasicRepo~K, V~ {
        <<abstract>>

        add(item: V)* ErisResult~K~
        get(key: K)* ErisResult~V_or_None~
    }

    class Repo~K, V~ {
        <<abstract>>

        update(key: K, item: V)* ErisResult~V~
        remove(key: K)* ErisResult~V_or_None~
    }

    class TaggedRepo~K, V, Tag~ {
        <<abstract>>

        get_by_tag(tag: Tag)* ErisResult~VList_or_None~
        remove_by_tag(tag: Tag)* ErisResult~VList_or_None~
    }

    class GreatDayRepo~str, T, Todo~ {
        <<concrete>>
    }

    class UnitOfWork~R~ {
        <<abstract>>

        repo: R

        __enter__()* Self
        __exit__()* None
        commit()* None
        rollback()* None
    }

    class GreatDaySession~GreatDayRepo~ {
        <<concrete>>
    }

    Repo --|> BasicRepo: inherits
    TaggedRepo --|> Repo: inherits
    UnitOfWork --* "1" BasicRepo: contains
    GreatDayRepo --|> TaggedRepo: inherits
    GreatDaySession --|> UnitOfWork: inherits
    GreatDaySession --* "1" GreatDayRepo: contains
```

[1]: https://github.com/bbugyi200/magodo
[2]: https://github.com/bbugyi200/potoroo
[3]: https://github.com/mermaid-js/mermaid
