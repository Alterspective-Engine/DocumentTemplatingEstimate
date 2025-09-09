import request from 'supertest';
import { createApp, createPool } from '../app';

jest.setTimeout(30000);

describe('Live DB E2E', () => {
  const pool = createPool();
  const app = createApp(pool);

  afterAll(async () => {
    await pool.end();
  });

  it('GET /api/health returns ok', async () => {
    const res = await request(app).get('/api/health').expect(200);
    expect(res.body).toHaveProperty('status', 'ok');
  });

  it('GET /api/stats/overview returns expected keys (live DB)', async () => {
    const res = await request(app).get('/api/stats/overview').expect(200);
    const body = res.body;
    expect(body).toHaveProperty('total_documents');
    expect(body).toHaveProperty('total_fields');
    expect(body).toHaveProperty('total_templates');
    expect(body).toHaveProperty('matched_templates');
    expect(body).toHaveProperty('complexity_levels');
    expect(body).toHaveProperty('unique_precedents');
    expect(body).toHaveProperty('match_rate');
  });

  it('GET /api/templates returns paginated data (live DB)', async () => {
    const res = await request(app).get('/api/templates?limit=1&offset=0').expect(200);
    expect(res.body).toHaveProperty('templates');
    expect(Array.isArray(res.body.templates)).toBe(true);
    expect(res.body).toHaveProperty('total');
  });
});

