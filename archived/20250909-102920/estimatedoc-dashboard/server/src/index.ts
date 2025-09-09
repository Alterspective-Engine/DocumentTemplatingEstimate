import { createApp, createPool } from './app';

const port = process.env.PORT || 3001;
const pool = createPool();
const app = createApp(pool);

app.listen(port, () => {
  // eslint-disable-next-line no-console
  console.log(`Server running at http://localhost:${port}`);
});
