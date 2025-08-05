from typing import cast

import frappe

from otto.lib.session import Session


def print_stats(sessions: list[Session]):
	total_cost = 0
	total_llm_calls = 0
	total_input_tokens = 0
	total_output_tokens = 0
	total_duration = 0

	for session in sessions:
		stats = session.get_stats()
		if not stats:
			continue

		cost_val = stats.get("cost", 0)
		llm_calls_val = stats.get("llm_calls", 0)
		input_tokens_val = stats.get("total_input_tokens", 0)
		output_tokens_val = stats.get("total_output_tokens", 0)
		duration_val = stats.get("duration", 0)

		cost = float(cost_val) if isinstance(cost_val, int | float) else 0.0
		llm_calls = int(llm_calls_val) if isinstance(llm_calls_val, int | float) else 0
		input_tokens = int(input_tokens_val) if isinstance(input_tokens_val, int | float) else 0
		output_tokens = int(output_tokens_val) if isinstance(output_tokens_val, int | float) else 0
		duration = float(duration_val) if isinstance(duration_val, int | float) else 0.0

		# Add to totals
		total_cost += cost
		total_llm_calls += llm_calls
		total_input_tokens += input_tokens
		total_output_tokens += output_tokens
		total_duration += duration

	print(f"Cost: ${total_cost:.6f}", end="\t")
	print(f"LLM Calls: {total_llm_calls}", end="\t")
	print(f"Input Tokens: {total_input_tokens:,}", end="\t")
	print(f"Output Tokens: {total_output_tokens:,}", end="\t")
	print(f"Duration: {total_duration:.2f}s")


def delete_sessions(sessions: list[Session]):
	for session in sessions:
		try:
			frappe.delete_doc("Otto Session", session.id, force=True)
		except Exception:
			pass  # Ignore cleanup errors

	frappe.db.commit()
