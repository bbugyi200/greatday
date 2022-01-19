### State Diagrams

#### State Diagram for the `greatday start` Command

The following diagram is kicked off when a user runs the `greatday start`
command. We assume that it has been `N` days since your tickler Todos were last
processed:

```mermaid
stateDiagram-v2
    state if_run_today <<choice>>

    process_ABC_priority: PROCESS TODOS | Todos which have a priority of 'A', 'B', or 'C'.
    process_daily: PROCESS TODOS | Todos added to today's daily file.
    collect_daily_fuzzy: Prompt for Todos (using fuzzy matching) to add to daily file.
    collect_daily_priority_D: Collect any todos that have a priority greater than or equal to 'D'.
    process_ticklers: PROCESS TODOS | Last N days of tickler Todos.
    inbox: PROCESS TODOS | Todos in your inbox (i.e. all Todos tagged with the @inbox context).

    state process_daily {
        [*] --> collect_daily_priority_D
        collect_daily_priority_D --> collect_daily_fuzzy
        collect_daily_fuzzy --> [*]
    }

    [*] --> process_ABC_priority
    process_ABC_priority --> process_ticklers
    process_ticklers --> if_run_today
    if_run_today --> process_daily: IF | This command was already run earlier today.
    if_run_today --> inbox: ELSE
    inbox --> process_daily
    process_daily --> [*]
```

#### State Diagram for Processing Todos

```mermaid
stateDiagram-v2
    state if_daily_check_failed <<choice>>

    check_todo_file: Run a series of tests against the todos remaing in this todo.txt file.
    ask_to_verify_todos: ASK | For verification / more information about Todo changes that we are unsure of.
    render_todo_file: Render a temporary todo.txt file after adding our newly collected Todos to it.
    save_daily_file: Commit the Todo changes made in our todo.txt file to the main Todo DB.
    edit_todo_file: Open this todo.txt file in a text editor.
    ask_if_ok_to_save: ASK | Is it OK to commit these changes?

    [*] --> render_todo_file: INPUT | List of Todo files + (optional) List of contexts (controls how Todos are grouped).
    render_todo_file --> edit_todo_file
    edit_todo_file --> check_todo_file: When the user closes her text editor...
    check_todo_file --> if_daily_check_failed
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

        from_line(line: str)$ ErisResult~Self~
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
classes interact.

Keep in mind the following notes while reviewing this diagram:

* `V_or_None` is meant to be `Optional[V]`. There seems to be a bug in
  [mermaid][3], however, that prevents us from using `Optional[V]` as a generic
  type.
* Similarly, `VList` is meant to be `List[V]`.
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

        get_by_tag(tag: Tag)* ErisResult~VList~
        remove_by_tag(tag: Tag)* ErisResult~VList~
    }

    class GreatRepo~str, T, Todo~ {
        <<concrete>>
    }

    class FileRepo~str, T~ {
        <<concrete>>
    }

    class UnitOfWork~R~ {
        <<abstract>>

        repo: R

        __enter__()* Self
        __exit__(etype, evalue, tback)* None
        commit()* None
        rollback()* None
    }

    class GreatSession~FileRepo~ {
        <<concrete>>
    }

    Repo --|> BasicRepo: inherits
    TaggedRepo --|> Repo: inherits
    UnitOfWork --* "1" BasicRepo: contains
    GreatRepo --|> TaggedRepo: inherits
    GreatRepo --o FileRepo: aggregates
    FileRepo --|> BasicRepo: inherits
    GreatSession --|> UnitOfWork: inherits
    GreatSession --* "1" GreatRepo: contains
    GreatSession --* "1" FileRepo: contains
```

[1]: https://github.com/bbugyi200/magodo
[2]: https://github.com/bbugyi200/potoroo
[3]: https://github.com/mermaid-js/mermaid
