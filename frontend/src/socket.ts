import { io } from "socket.io-client";
import csc from "../../../../sites/common_site_config.json";
import { logRealtime } from "./client/utils";
import type { RealtimeLog } from "./client/generated.types";

export function initSocket() {
  const host = window.location.hostname;
  const port = window.location.port ? `:${csc.socketio_port}` : "";
  const protocol = port ? "http" : "https";

  // @ts-ignore default_site not always available
  const siteName = import.meta.env.DEV ? csc.default_site : window.site_name;
  const url = `${protocol}://${host}${port}/${siteName}`;

  return io(url, {
    withCredentials: true,
    reconnectionAttempts: 5,
  });
}

const socket = initSocket();
if (import.meta.env.DEV) {
  socket.on("otto.log_realtime", (message: RealtimeLog) => {
    logRealtime(message);
  });
}

export default socket;
