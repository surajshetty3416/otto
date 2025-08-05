<div align="center" markdown="1">

<img src="./.github/assets/otto.png" alt="Otto logo" width="80" />
<h1>Otto</h1>

**Automation intelligence for the Frappe ecosystem**

<div>
    <picture>
        <img width="1402" alt="Otto Session Viewer Screenshot" src=".github/assets/otto-ss.png">
    </picture>
</div>

</div>

> [!WARNING]
>
> Otto is in very early stages of development, the application aspects of it are
> still under heavy experimentation.
>
> Nevertheless, you may use it as library in your own Frappe app to manage interaction
> with LLMs.
>
> [Library documentation](./otto/lib/docs/README.md) for reference.

### Current Features

- Handle LLM integration into your Frappe app by using Otto as a library.
- Use LLMs to handle task automation in your Frappe app.

### Under the hood

[Frappe Framework](https://github.com/frappe/frappe): A full-stack web application framework.

### Local Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI, first setup a Frappe bench directory and create a new site then:

```bash
# In you bench directory
bench get-app otto --branch develop
bench --site site-name install-app otto
```

## Links

- [Otto Lib Docs](./otto/lib/docs/README.md)

<br>
<br>
<div align="center">
	<a href="https://frappe.io" target="_blank">
		<picture>
			<source media="(prefers-color-scheme: dark)" srcset="https://frappe.io/files/Frappe-white.png">
			<img src="https://frappe.io/files/Frappe-black.png" alt="Frappe Technologies" height="28"/>
		</picture>
	</a>
</div>
