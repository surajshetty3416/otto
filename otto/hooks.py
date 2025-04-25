app_name = "otto"
app_title = "Otto"
app_publisher = "Alan Tom"
app_description = "Test app to validate ideas in Flow"
app_email = "alan@frappe.io"
app_license = "agpl-3.0"


# This dict is runtime updated by otto.doctype.otto_task.utils.update_doc_events
# a tentative dirty hack to avoid registering catchall event handlers for all
# doctypes and all events
# __START_DOC_EVENTS__
doc_events = {}
# __END_DOC_EVENTS__
