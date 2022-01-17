### State Diagram for the `greatday start` Command

The following diagram is kicked off when a user runs the `greatday start`
command. We assume that it has been `N` days since your tickler Todos were last
processed:

![diagram](./design-1.svg)

### Class Diagrams

#### Class Diagram for `Todo` Classes

Note that the generic type variable `T` is bound by the `AbstractTodo` protocol
(i.e. `T` must be an `AbstractTodo` type).

![diagram](./design-2.svg)
