app_name = "otto"
app_title = "Otto"
app_publisher = "Alan Tom"
app_description = "Automation intelligence for the Frappe ecosystem"
app_email = "alan@frappe.io"
app_license = "agpl-3.0"

add_to_apps_screen = [
	{
		"name": "otto",
		"logo": "/assets/otto/desk/otto-logo.svg",
		"title": "Otto",
		"route": "/app/otto",
	}
]


otto_task_handler = "otto.otto.doctype.otto_task.otto_task.common_handler"
doc_events = {
	"*": {
		"after_insert": otto_task_handler,
		"on_update": otto_task_handler,
		"on_delete": otto_task_handler,
		"on_submit": otto_task_handler,
		"on_cancel": otto_task_handler,
	}
}

export_python_type_annotations = True

website_route_rules = [
	{"from_route": "/otto/<path:app_path>", "to_route": "otto"},
]

fixtures = ["Otto LLM"]
email_css = ["/assets/otto/css/email.css"]
