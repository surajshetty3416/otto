Conventions followed in this project might not be consistent with those followed
in other Frappe apps. This file elucidates these conventions and the reasoning
behind them conventions.

Considering that the author is NOT omniscient, they may be prone to making daft
mistakes. If you find any convention to not be in good taste, please
[raise an issue](https://github.com/frappe/otto/issues/new).

<!--

Frontend conventions:
- all backend calls should go through `otto/api`
- `otto/api` should not have any business logic this will be in controller files
- all exposed methods in `otto/api` should have a well typed signature
- no direct exposure of backend shapes and schemas to the frontend
- frontend is not the logic layer, just the presentation
- `otto/api` readies the backend data for the frontend

not all applications built on Frappe Framework are and ERP and so your schema
design is not what should be shipped to the user. trying to construct schema for
user consumption, convenience, app interface will leads to sub par decisions.

and so by using otto/api, we separate the concerns of user interface and schema
api shapes the schema for the interface. this is swe 201.
-->
