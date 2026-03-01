import { db } from "@/lib/db";
import { NextRequest, NextResponse } from "next/server";

/**
 * Handles GET requests for the Daytrade Screener.
 * This screener finds stocks with a high ratio of aggressive buy trades (HAKA)
 * in the last N minutes, indicating strong buying pressure.
 * 
 * Query Params:
 * - minutes: (optional) The number of minutes to look back. Defaults to 30.
 * - limit: (optional) The number of stocks to return. Defaults to 10.
 * - min_trades: (optional) The minimum number of trades for a stock to be considered. Defaults to 20.
 */
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const minutes = searchParams.get("minutes") || '30';
  const limit = searchParams.get("limit") || '10';
  const minTrades = searchParams.get("min_trades") || '20';

  try {
    const client = await db.connect();
    try {
      // This query identifies stocks with high recent buying pressure.
      // It calculates the ratio of 'HAKA' (aggressive buy) trades to total trades
      // for each stock in a recent time window.
      const query = `
        WITH recent_trades AS (
          SELECT
            symbol,
            trade_type,
            price,
            volume
          FROM
            trades
          WHERE
            timestamp >= NOW() - INTERVAL '1 minute' * $1
        ),
        trade_counts AS (
          SELECT
            symbol,
            COUNT(*) as total_trades,
            SUM(CASE WHEN trade_type = 'HAKA' THEN 1 ELSE 0 END) as haka_trades
          FROM
            recent_trades
          GROUP BY
            symbol
        )
        SELECT
          symbol,
          haka_trades::float / total_trades::float as haka_ratio,
          total_trades
        FROM
          trade_counts
        WHERE
          total_trades > $2
        ORDER BY
          haka_ratio DESC,
          total_trades DESC
        LIMIT $3;
      `;
      const result = await client.query(query, [minutes, minTrades, limit]);
      
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
      { success: false, error: "Failed to run Daytrade Screener.", details: errorMessage },
      { status: 500 }
    );
  }
}
