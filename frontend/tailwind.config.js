import preset from "./tailwind/preset";

/** @type {import('tailwindcss').Config} */
export default {
	presets: [preset],
	content: ["./index.html", "./src/**/*.{vue,js,ts,jsx,tsx}"],
	theme: {
		extend: {},
	},
	plugins: [],
};
