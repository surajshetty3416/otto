import vue from "@vitejs/plugin-vue";
import fs from "fs";
import path from "path";
import { defineConfig, Plugin, type ProxyOptions } from "vite";

const fallbackFrappeServerPort = 8001;
const outDir = "../otto/public/frontend";

// https://vite.dev/config/
export default defineConfig(() => {
  const frappeServerPort = getFrappeServerPort();

  // Used in dev mode api calls are routed to frappe server
  const proxy: Record<string, ProxyOptions> = {};
  proxy["/api"] = {
    target: `http://127.0.0.1:${frappeServerPort}`,
    secure: false,
    cookieDomainRewrite: "",
    rewriteWsOrigin: true,
    ws: true,
  };

  return {
    plugins: [vue(), postBuild()],
    base: process.env.NODE_ENV === 'production' ? "/assets/otto/frontend/" : "/",
    build: {
      outDir,
      emptyOutDir: true,
    },
    server: {
      port: frappeServerPort + 80,
      proxy,
    },
  };
});

function getFrappeServerPort(): number {
  let currentDir = path.resolve(".");
  while (currentDir !== "/") {
    if (
      !fs.existsSync(path.join(currentDir, "sites")) ||
      !fs.existsSync(path.join(currentDir, "apps"))
    ) {
      currentDir = path.resolve(currentDir, "..");
      continue;
    }

    const configPath = path.join(
      currentDir,
      "sites",
      "common_site_config.json"
    );

    if (!fs.existsSync(configPath)) {
      return fallbackFrappeServerPort;
    }

    const contents = fs.readFileSync(configPath, "utf-8");
    const config = JSON.parse(contents);
    const port = Number(config?.webserver_port);
    return Number.isNaN(port) ? fallbackFrappeServerPort : port;
  }

  return fallbackFrappeServerPort;
}

// Custom plugin to log when build is done
function postBuild(): Plugin {
  function closeBundle() {
    const indexHtmlPath = path.join(outDir, "index.html");
    const ottoHtmlPath = path.join("../otto/www/otto", "index.html");

    try {
      fs.renameSync(indexHtmlPath, ottoHtmlPath);
    } catch (error) {
      console.error("failed to move index.html to otto.html:", error);
    }
  }

  return {
    name: "post-build",
    apply: "build",
    enforce: "post",
    closeBundle,
  };
}
