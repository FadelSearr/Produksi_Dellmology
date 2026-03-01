import { db } from "@/lib/db";
import { NextRequest, NextResponse } from "next/server";

/**
 * Handles GET requests for the Swing Screener.
 * This screener finds stocks with the highest net accumulation over the last N days.
 * 
 * Query Params:
 * - days: (optional) The number of days to look back. Defaults to 7.
 * - limit: (optional) The number of stocks to return. Defaults to 10.
 */
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const days = searchParams.get("days") || '7';
  const limit = searchParams.get("limit") || '10';

  try {
    const client = await db.connect();
    try {
      // This query calculates the total net buy value for each symbol over the last N days
      // and returns the top M symbols.
      const query = `
        SELECT
          symbol,
          SUM(net_buy_value) as total_net_accumulation
        FROM
          broker_summaries
        WHERE
          date >= NOW() - INTERVAL '1 day' * $1
        GROUP BY
          symbol
        ORDER BY
          total_net_accumulation DESC
        LIMIT $2;
      `;
      const result = await client.query(query, [days, limit]);
      
      return NextResponse.json(
        { success: true, data: result.rows },
        { status: 200 }
      );
    } finally {
      client.release();
    }
  } catch (error) {
    const errorMessage =
      error instanceof Error ? error.message : "An unknown error occurred";
    return NextResponse.json(
      { success: false, error: "Failed to run Swing Screener.", details: errorMessage },
      { status: 500 }
    );
  }
}
