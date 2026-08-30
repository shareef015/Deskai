import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    incidents: {
      executor: 'ramping-arrival-rate',
      startRate: 5,
      timeUnit: '1s',
      preAllocatedVUs: 50,
      maxVUs: 500,
      stages: [
        { target: 30, duration: '2m' },
        { target: 60, duration: '5m' },
        { target: 120, duration: '5m' },
        { target: 0, duration: '1m' },
      ],
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<250', 'p(99)<500'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';

export default function () {
  const headers = {
    'Content-Type': 'application/json',
    'X-Load-Test': 'performance',
    Authorization: `Bearer ${__ENV.LOAD_TEST_TOKEN || ''}`,
  };
  const response = http.get(`${BASE_URL}/health`, { headers, redirects: 0 });
  check(response, { 'health returned expected status': (r) => [200, 401, 403].includes(r.status) });
  sleep(0.05);
}
