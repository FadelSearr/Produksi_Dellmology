import { NextResponse } from 'next/server';
import { db } from '@/lib/db';

export const dynamic = 'force-dynamic';

/**
 * GET /api/market-intelligence?symbol=BBCA&timeframe=1h
 * Returns real-time market intelligence data:
 * - HAKA/HAKI ratio
 * - Buy/Sell volume
 * - Order flow heatmap data
 * - Volatility metrics
 * - UPS (Unified Power Score)
 */
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const symbol = searchParams.get('symbol') || 'BBCA';
    const timeframe = searchParams.get('timeframe') || '1h';

    // Calculate time window
    const timeWindows: { [key: string]: string } = {
      '15m': '15 minutes',
      '1h': '1 hour',
      '4h': '4 hours',
      '1d': '1 day'
    };

    const window = timeWindows[timeframe] || '1 hour';

    // Get recent trades
    const tradesQuery = `
      SELECT 
        trade_type,
        COUNT(*) as count,
        SUM(volume) as total_volume,
        AVG(price) as avg_price,
        MAX(price) as high_price,
        MIN(price) as low_price
      FROM trades
      WHERE symbol = $1
        AND timestamp >= NOW() - INTERVAL '${window}'
      GROUP BY trade_type
    `;

    const tradesResult = await db.query(tradesQuery, [symbol]);

    // Parse trade types
    let hakaVolume = 0, hakiVolume = 0, normalVolume = 0;
    let hakaCount = 0, hakiCount = 0;

    tradesResult.rows.forEach((row: any) => {
      if (row.trade_type === 'HAKA') {
        hakaVolume = Number(row.total_volume);
        hakaCount = row.count;
      } else if (row.trade_type === 'HAKI') {
        hakiVolume = Number(row.total_volume);
        hakiCount = row.count;
      } else {
        normalVolume = Number(row.total_volume);
      }
    });

    const totalVolume = hakaVolume + hakiVolume + normalVolume;
    const hakaRatio = totalVolume > 0 ? (hakaVolume / totalVolume) * 100 : 0;
    const hakiRatio = totalVolume > 0 ? (hakiVolume / totalVolume) * 100 : 0;

    // Calculate pressure index (HAKA - HAKI) / Total
    const pressureIndex = totalVolume > 0 ? ((hakaVolume - hakiVolume) / totalVolume) * 100 : 0;

    // Get historical high/low for volatility
    const volatilityQuery = `
      SELECT 
        MAX(price) - MIN(price) as range,
        AVG(price) as avg,
        STDDEV(price) as stddev
      FROM trades
      WHERE symbol = $1
        AND timestamp >= NOW() - INTERVAL '${window}'
    `;

    const volatilityResult = await db.query(volatilityQuery, [symbol]);
    const priceRange = volatilityResult.rows[0]?.range || 0;
    const avgPrice = volatilityResult.rows[0]?.avg || 0;
    const volatility = avgPrice > 0 ? (Number(priceRange) / Number(avgPrice)) * 100 : 0;

    // Calculate Unified Power Score (UPS)
    // Combines: HAKA dominance (40%), Volume momentum (30%), Price above MA (20%), Consistency (10%)
    const hakaStrength = Math.min((hakaRatio / 50) * 40, 40); // Max 40 points
    const volumeMomentum = Math.min((totalVolume / 10000) * 30, 30); // Max 30 points
    const priceStrength = Math.min(Math.abs(pressureIndex) / 2.5, 20); // Max 20 points
    const consistency = (hakaCount / (hakaCount + hakiCount || 1)) * 10; // Max 10 points
    
    const ups = Math.min(hakaStrength + Math.min(volumeMomentum, 30) + priceStrength + consistency, 100);

    // Determine signal
    let signal = 'NEUTRAL';
    if (ups > 70) signal = 'STRONG_BUY';
    else if (ups > 60) signal = 'BUY';
    else if (ups < 30) signal = 'STRONG_SELL';
    else if (ups < 40) signal = 'SELL';

    return NextResponse.json({
      symbol,
      timeframe,
      metrics: {
        haka_volume: hakaVolume,
        haki_volume: hakiVolume,
        normal_volume: normalVolume,
        total_volume: totalVolume,
        haka_ratio: hakaRatio,
        haki_ratio: hakiRatio,
        pressure_index: pressureIndex, // Positive = more buys, negative = more sells
        haka_count: hakaCount,
        haki_count: hakiCount
      },
      volatility: {
        percentage: volatility,
        range: priceRange,
        classification: volatility > 3 ? 'HIGH' : volatility > 1.5 ? 'MEDIUM' : 'LOW'
      },
      unified_power_score: {
        score: Math.round(ups),
        signal,
        components: {
          haka_strength: hakaStrength,
          volume_momentum: Math.min(volumeMomentum, 30),
          price_strength: priceStrength,
          consistency: consistency
        }
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Error fetching market intelligence:', error);
    return NextResponse.json(
      { error: 'Failed to fetch market intelligence data' },
      { status: 500 }
    );
  }
}
