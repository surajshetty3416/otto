# Otto Lib

When installed along side other Frappe apps, the code in this folder allows the
other apps to use Otto as an LLM library.

As of now, the library methods allows the caller to invoke one of the supported
LLMs. By doing so Otto will manage the provider API aggregations, managing of
Session, etc. Since Session management is backed by a DocType, this needs to a
Frappe app.
