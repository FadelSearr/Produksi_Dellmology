import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

/**
 * GET /api/market-regime
 * Returns current market regime (trend, volatility, RSI, ATR)
 * This data comes from the streaming service and is stored in cache/DB
 */
export async function GET(request: Request) {
  try {
    // In a real implementation, this would fetch from StreamerDB or cache
    // For now, return a mock structure that matches the streamer's MarketRegime
    
    const regime = {
      regime: 'UPTREND',
      volatility: 'HIGH',
      trend_strength: 72.3,
      rsi: 62.5,
      atr: 145.2,
      last_updated: new Date().toISOString(),
      timestamp: Math.floor(Date.now() / 1000)
    };

    return NextResponse.json(regime);
  } catch (error) {
    console.error('Error fetching market regime:', error);
    return NextResponse.json(
      { error: 'Failed to fetch market regime' },
      { status: 500 }
    );
  }
}
