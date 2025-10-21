from pathlib import Path

import click
from frappe import get_app_path

import otto.commands.typegen as typegen


@click.command("generate-types")
@click.option("--app", default="otto", type=click.STRING, help="App to generate types for")
@click.option("--api", is_flag=True, help="Generate API types")
@click.option("--doctype", is_flag=True, help="Generate DocType types")
@click.option("--exported", is_flag=True, help="Generate exported types marked with `# @export`")
@click.option(
	"--out",
	default="frontend/src/client/generated.types.ts",
	type=click.STRING,
	help="Path under the given app to save these types",
)
def generate_types(
	app: str,
	api: bool,
	doctype: bool,
	exported: bool,
	out: str,
):
	if not api and not doctype and not exported:
		api = True
		doctype = True
		exported = True

	if app != "otto" and api:
		return print(click.style("API types can only be generated for the otto app", fg="red"))

	ttype = []
	if doctype:
		ttype.append("DocType")
	if api:
		ttype.append("API")
	if exported:
		ttype.append("Exported")

	confirmed = click.confirm(
		"\n".join(
			[
				f"Generate {click.style(', '.join(ttype), fg='blue')} types for app {click.style(app, fg='blue')} with",
				f"output at {click.style(app + '/' + out, fg='blue')}?",
			]
		)
	)

	if not confirmed:
		return None
	print()

	if doctype and typegen.generate_doctype_types(app, out):
		print(click.style("DocType types generated successfully\n", fg="green"))

	app_path = Path(get_app_path(app))
	found_types = typegen.populate_found_types(app_path)

	if api and typegen.generate_api_types(out, found_types):
		print(click.style("API types generated successfully\n", fg="green"))

	if exported and typegen.generate_exported_types(out, found_types):
		print(click.style("Exported types generated successfully\n", fg="green"))

	return None


commands = [generate_types]
