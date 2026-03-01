import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

// Interface for global market data
interface GlobalMarketData {
  gold: number;
  coal: number;
  nickel: number;
  ihsg: number;
  dji: number;
  change_gold: number;
  change_coal: number;
  change_nickel: number;
  change_ihsg: number;
  change_dji: number;
  last_updated: string;
}

/**
 * GET /api/global-correlation
 * Returns global commodities and indices prices
 * Should fetch from yfinance or similar API every 5 minutes
 */
export async function GET(request: Request) {
  try {
    // Mock data - in production, this would call yfinance API
    const mockData: GlobalMarketData = {
      gold: 2150.50,          // USD/oz
      coal: 85.30,            // USD/ton
      nickel: 8.95,           // USD/lb
      ihsg: 7240.50,          // Points
      dji: 39845.30,          // Points
      change_gold: 0.45,      // %
      change_coal: -1.20,     // %
      change_nickel: 2.10,    // %
      change_ihsg: 1.80,      // %
      change_dji: -0.35,      // %
      last_updated: new Date().toISOString()
    };

    // Optionally add sentiment from market data
    const sentiment = mockData.change_ihsg > 0 ? 'BULLISH' : 'BEARISH';

    return NextResponse.json({
      ...mockData,
      global_sentiment: sentiment,
      correlation_strength: 0.72  // How correlated IDX is with global markets
    });
  } catch (error) {
    console.error('Error fetching global correlation data:', error);
    return NextResponse.json(
      { error: 'Failed to fetch global market data' },
      { status: 500 }
    );
  }
}

/**
 * POST /api/global-correlation/update
 * Manually trigger update of global market data (admin only)
 */
export async function POST(request: Request) {
  try {
    const body = await request.json();
    
    // Validate request source (should be from streamer or scheduled job)
    const apiKey = request.headers.get('x-api-key');
    if (apiKey !== process.env.INTERNAL_API_KEY) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    // Store the data in cache or DB
    // This would be called by a background job every 5 minutes
    
    return NextResponse.json({
      success: true,
      message: 'Global market data updated'
    });
  } catch (error) {
    console.error('Error updating global correlation:', error);
    return NextResponse.json(
      { error: 'Failed to update global data' },
      { status: 500 }
    );
  }
}
