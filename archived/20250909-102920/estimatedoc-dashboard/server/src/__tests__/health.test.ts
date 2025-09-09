import request from 'supertest';
import { createApp, createPool } from '../app';

describe('health endpoint', () => {
  const pool = createPool();
  const app = createApp(pool);

  afterAll(async () => {
    await pool.end();
  });

  it('GET /api/health returns ok', async () => {
    const res = await request(app).get('/api/health').expect(200);
    expect(res.body).toHaveProperty('status', 'ok');
    expect(res.body).toHaveProperty('timestamp');
  });
});

