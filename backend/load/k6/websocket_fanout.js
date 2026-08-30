import ws from 'k6/ws';
import { check } from 'k6';

export const options = {
  vus: Number(__ENV.VUS || 100),
  duration: __ENV.DURATION || '2m',
};

const WS_URL = __ENV.WS_URL || 'ws://127.0.0.1:8000/ws/events';
export default function () {
  const response = ws.connect(WS_URL, {}, (socket) => {
    socket.on('open', () => socket.send(JSON.stringify({ type: 'ping' })));
    socket.setTimeout(() => socket.close(), 1000);
  });
  check(response, { 'websocket handshake does not 5xx': (r) => r && r.status < 500 });
}
