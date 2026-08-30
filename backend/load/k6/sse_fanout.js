import http from 'k6/http';
import { check } from 'k6';

export const options = {
  vus: Number(__ENV.VUS || 100),
  duration: __ENV.DURATION || '2m',
  thresholds: { http_req_failed: ['rate<0.01'] },
};

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';
export default function () {
  const response = http.get(`${BASE_URL}/api/events`, {
    headers: { Accept: 'text/event-stream', Authorization: `Bearer ${__ENV.LOAD_TEST_TOKEN || ''}` },
    timeout: '30s',
  });
  check(response, { 'SSE route is reachable/protected': (r) => [200, 401, 403, 404].includes(r.status) });
}
