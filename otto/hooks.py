app_name = "otto"
app_title = "Otto"
app_publisher = "Alan Tom"
app_description = "Test app to validate ideas in Flow"
app_email = "alan@frappe.io"
app_license = "agpl-3.0"

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

fixtures = ["Otto LLM"]
