# Otto

> [!NOTE]
>
> The application aspect of Otto has barely begun, a significant work in
> progress that can only be called an experiment as of now.
>
> Nevertheless, you may use it's library features in your own Frappe app
> to build LLM capabilities. See [docs for reference](./otto/lib/docs/README.md).

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app https://github.com/frappe/otto --branch develop
bench install-app otto
```

<!--
### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/otto
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade
-->

### License

agpl-3.0
