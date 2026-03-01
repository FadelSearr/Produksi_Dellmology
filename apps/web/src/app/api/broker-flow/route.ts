import { NextResponse } from 'next/server';
import { db } from '@/lib/db';

export const dynamic = 'force-dynamic';

/**
 * GET /api/broker-flow?symbol=BBCA&days=7&filter=all
 * Returns broker flow analysis for a symbol
 * Filters: 'whale', 'retail', 'smart_money', 'mix'
 * Days: 1, 7, 14, 21
 */
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const symbol = searchParams.get('symbol') || 'BBCA';
    const days = parseInt(searchParams.get('days') || '7');
    const filter = searchParams.get('filter') || 'mix';

    // Query broker summaries from database
    const query = `
      SELECT 
        broker_id,
        SUM(net_buy_value) as total_net_buy,
        AVG(avg_buy_price) as avg_buy_price,
        COUNT(DISTINCT date) as active_days,
        array_agg(net_buy_value ORDER BY date) as daily_data
      FROM broker_summaries
      WHERE symbol = $1
        AND date >= NOW()::date - $2::interval
      GROUP BY broker_id
      ORDER BY ABS(total_net_buy) DESC
      LIMIT 15
    `;

    const result = await db.query(query, [symbol, `${days} days`]);

    const brokers = result.rows.map((row: any) => ({
      broker_id: row.broker_id,
      net_buy_value: row.total_net_buy,
      active_days: row.active_days,
      consistency_score: (row.active_days / days) * 100,
      avg_buy_price: row.avg_buy_price,
      daily_heatmap: row.daily_data,
      is_whale: Math.abs(row.total_net_buy) > 5000000000, // > 5T IDR
      is_retail: Math.abs(row.total_net_buy) < 500000000    // < 500M IDR
    }));

    // Calculate Z-Scores
    const netValues = brokers.map(b => b.net_buy_value);
    const mean = netValues.reduce((a, b) => a + b, 0) / netValues.length;
    const stdDev = Math.sqrt(
      netValues.reduce((sq, n) => sq + Math.pow(n - mean, 2), 0) / netValues.length
    );

    const brokersWithZScore = brokers.map((b: any) => ({
      ...b,
      z_score: stdDev === 0 ? 0 : (b.net_buy_value - mean) / stdDev,
      is_anomalous: stdDev === 0 ? false : Math.abs((b.net_buy_value - mean) / stdDev) > 2
    }));

    // Apply filter
    let filtered = brokersWithZScore;
    if (filter === 'whale') {
      filtered = brokersWithZScore.filter(b => b.is_whale);
    } else if (filter === 'retail') {
      filtered = brokersWithZScore.filter(b => b.is_retail);
    } else if (filter === 'smart_money') {
      filtered = brokersWithZScore.filter(b => b.is_anomalous && b.consistency_score > 50);
    }

    // Detect wash sales
    const totalVolume = result.rows.length;
    const avgNetValue = Math.abs(mean);
    const totalAccumulation = Math.abs(netValues.reduce((a, b) => a + b, 0));
    const washSaleScore = totalVolume > 0 
      ? (1 - totalAccumulation / (totalVolume * 1000000000)) * 100 
      : 0;

    return NextResponse.json({
      symbol,
      days,
      filter,
      brokers: filtered,
      stats: {
        total_brokers: brokersWithZScore.length,
        whales: brokersWithZScore.filter(b => b.is_whale).length,
        retail: brokersWithZScore.filter(b => b.is_retail).length,
        avg_net_value: mean,
        std_deviation: stdDev,
        wash_sale_score: Math.min(washSaleScore, 100),
      },
      last_updated: new Date().toISOString()
    });

  } catch (error) {
    console.error('Error fetching broker flow:', error);
    return NextResponse.json(
      { error: 'Failed to fetch broker flow data' },
      { status: 500 }
    );
  }
}
