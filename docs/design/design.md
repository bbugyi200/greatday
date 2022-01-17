### State Diagram for the `greatday start` Command

The following diagram is kicked off when a user runs the `greatday start`
command. We assume that it has been `N` days since your tickler Todos were last
processed:

![diagram](./design-1.svg)

### Class Diagrams

This section contains class diagrams used to help design / document greatday.

Note that the generic type variable `T` is bound by the `AbstractTodo`
protocol (i.e. `T` must be an `AbstractTodo` type).

#### Class Diagram for `Todo` Classes

The following diagram illustrates how the various [magodo][1] `Todo` classes
interact.

![diagram](./design-2.svg)

#### Class Diagram for `Repo` Classes

The following diagram illustrates how the various [potoroo][2] `Repo` and `UnitOfWork`
(Unit-of-Work) classes interact.

Keep in mind the following notes while reviewing:

* `VorNone` is meant to be `Optional[V]`. There seems to be a bug in
  [mermaid][3], however, that prevents us from using `Optional[V]` as a generic
  type.
* The type variable `U` is bound by the `UnitOfWork` class.

![diagram](./design-3.svg)

[1]: https://github.com/bbugyi200/magodo
[2]: https://github.com/bbugyi200/potoroo
[3]: https://github.com/mermaid-js/mermaid
