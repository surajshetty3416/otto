/** @type {import('tailwindcss').Config} */
export default {
	presets: [require("./tailwind/preset")],
	content: ["./index.html", "./src/**/*.{vue,js,ts,jsx,tsx}"],
	theme: {
		extend: {},
	},
	plugins: [],
};
