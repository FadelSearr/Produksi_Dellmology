import { db } from '@/lib/db';
import { NextResponse } from 'next/server';
import { NextRequest } from 'next/server';

/**
 * POST /api/update-token
 * Receives and stores a new session token from the browser extension.
 * This acts as the bridge between the user's authenticated session and the backend services.
 */
export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { token, expires_at } = body;

    if (!token || typeof token !== 'string') {
      return NextResponse.json({ error: 'A valid token must be provided.' }, { status: 400 });
    }

    // Use parameterized query to prevent SQL injection.
    const query = `
      INSERT INTO config (key, value, expires_at)
      VALUES ('session_token', $1, $2)
      ON CONFLICT (key) DO UPDATE
      SET 
        value = EXCLUDED.value,
        expires_at = EXCLUDED.expires_at,
        updated_at = NOW();
    `;

    // The expires_at could be null or a valid date string.
    // The database column is TIMESTAMPTZ, which can handle ISO 8601 format.
    await db.query(query, [token, expires_at || null]);

    return NextResponse.json({ message: 'Token updated successfully.' });

  } catch (error) {
    console.error('Error updating token:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
