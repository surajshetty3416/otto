Conventions followed in this project might not be consistent with those followed
in other Frappe apps. This file elucidates these conventions and the reasoning
behind them conventions.

Considering that the author is NOT omniscient, they may be prone to making daft
mistakes. If you find any convention to not be in good taste, please
[raise an issue](https://github.com/frappe/otto/issues/new).

## Index

- [`DocType.new`](#doctypenew)
- [`otto.new`](#ottonew)
- [`otto.get`](#ottoget)
- [Avoid raising exceptions](#avoid-raising-exceptions)
- [Otto and CT DocType prefix and suffix](#otto-and-ct-doctype-prefix-and-suffix)

<!--

Frontend conventions:
- all backend calls should go through `otto/api`
- `otto/api` should not have any business logic this will be in controller files
- all exposed methods in `otto/api` should have a well typed signature
- no direct exposure of backend shapes and schemas to the frontend
- frontend is not the logic layer, just the presentation
- `otto/api` readies the backend data for the frontend
- keyboard first UI, everything should be accessible via keyboard

not all applications built on Frappe Framework are and ERP and so your schema
design is not what should be shipped to the user. trying to construct schema for
user consumption, convenience, app interface will leads to sub par decisions.

and so by using otto/api, we separate the concerns of user interface and schema
api shapes the schema for the interface. this is swe 201.
-->

## `DocType.new`

Instead of using `frappe.new_doc` or `frappe.get_doc`, the project instead uses
defines a `staticmethod` called `new` on the controller class of the DocType and
uses it instead. Every `new` method saves the doc before returning it.

**Reason**:

- Allows explicit control over doc creation (i.e. valid and invalid create invocations)
- Allows typing the returned doc

## `otto.new`

Instead of using `frappe.new_doc`, `otto.new` is used. Example:

```python
log = otto.new(NotificationLog)
```

**Reason**: allows typing the returned doc

## `otto.get`

Instead of using `frappe.get_doc` or `frappe.get_cached_doc`, `otto.get` is
used. Example:

```python
task = otto.get(OttoTask, name, cache=True)
```

**Reason**: returned doc is typed allowing type safety to all callers

## Avoid raising exceptions

If a wrong behavior or value is expected then instead of raising an exception,
the reason for wrong behavior should be returned sensibly up the call stack.

**Reason:** Raising an exception may cause control flow to jump to an unexpected
place in the call stack. This is lazy engineering when used for expected
incorrect behavior. It foists responsibility on some random caller up the call
stack without accurately communicating what's wrong.

## Otto and CT DocType prefix and suffix

_Otto_ is used as a prefix for all DocTypes defined under otto and _CT_ is
used as a suffix for all child tables DocTypes defined under otto.

**Reason**: easier to identify and _namespace_ DocType when noticed in the wild.
