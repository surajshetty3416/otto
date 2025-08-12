history.replaceState(null, "", "/otto_feedback"); // Hide query params

document.addEventListener("DOMContentLoaded", function () {
	const form = document.getElementById("feedbackForm");
	const thumbButtons = document.querySelectorAll(".thumb-btn");

	const context = JSON.parse(document.getElementById("context-data").textContent);
	const session = context.session;
	const name = context.name;

	let selectedValue = context.value || 0;
	for (const button of thumbButtons) {
		if (button.hasAttribute("selected")) {
			button.classList.add("selected");
		}

		button.addEventListener("click", function () {
			const value = parseInt(this.dataset.value);

			if (selectedValue === value) {
				selectedValue = 0;
				this.classList.remove("selected");
			} else {
				selectedValue = value;
				thumbButtons.forEach((btn) => btn.classList.remove("selected"));
				this.classList.add("selected");
			}
		});
	}

	form.addEventListener("submit", async function (e) {
		e.preventDefault();

		const comment = document.getElementById("comment").value.trim();
		const submitBtn = document.getElementById("submitBtn");

		const params = new URLSearchParams();
		if (name) params.append("name", name);
		if (selectedValue !== 0) params.append("value", selectedValue.toString());
		if (comment) params.append("comment", comment);
		if (session) params.append("session", session);

		submitBtn.disabled = true;
		submitBtn.textContent = "Submitting";

		let data = null;
		try {
			const url = encodeURI("/api/method/otto.api.log_feedback?" + params.toString());
			const res = await fetch(url);
			const json = await res.json();
			data = json.message;
		} catch (error) {
			frappe.toast({ message: "Failed to submit feedback", indicator: "red" });
			submitBtn.textContent = "Submit";
			submitBtn.disabled = false;
			console.error(error);
			return;
		}

		if (data.message === "success") {
			submitBtn.textContent = "Submitted";
			frappe.toast({ message: "Feedback submitted, thank you!", indicator: "green" });
			setTimeout(() => {
				window.close();
				window.location.href = "/"; // fallback
			}, 2000);
		} else {
			submitBtn.textContent = "Submit";
			submitBtn.disabled = false;
			frappe.msgprint({
				title: "Error submitting feedback",
				message: data.reason || "Unknown error occurred",
				indicator: "red",
			});
		}
	});
});
