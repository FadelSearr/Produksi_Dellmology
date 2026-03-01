import { Pool } from 'pg';

// TODO: Move connection details to environment variables (.env.local)
const DATABASE_URL = 'postgresql://admin:password@localhost:5433/dellmology';

let pool: Pool;

// Use a global variable in development to prevent connection pool exhaustion during hot-reloads.
// In production, the app is initialized once, so this isn't an issue.
if (process.env.NODE_ENV === 'production') {
  pool = new Pool({
    connectionString: DATABASE_URL,
    ssl: {
      rejectUnauthorized: false, // Required for some cloud providers, adjust as needed.
    },
  });
} else {
  // Ensure the pool is created only once in development.
  if (!global._pgPool) {
    global._pgPool = new Pool({
      connectionString: DATABASE_URL,
    });
  }
  pool = global._pgPool;
}

export const db = pool;
