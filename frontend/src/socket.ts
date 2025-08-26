import { io } from "socket.io-client";
import csc from "../../../../sites/common_site_config.json";

export function initSocket() {
  const host = window.location.hostname;
  const siteName = import.meta.env.DEV ? csc.default_site : window.site_name;
  const port = window.location.port ? `:${csc.socketio_port}` : "";
  const protocol = port ? "http" : "https";
  const url = `${protocol}://${host}${port}/${siteName}`;

  return io(url, {
    withCredentials: true,
    reconnectionAttempts: 5,
  });
}

export default initSocket();
