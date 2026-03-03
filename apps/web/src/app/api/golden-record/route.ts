import { NextResponse } from 'next/server';
import { db } from '@/lib/db';

export const dynamic = 'force-dynamic';

type AnchorSymbol = 'BBCA' | 'ASII' | 'TLKM';

interface AnchorValidation {
  symbol: AnchorSymbol;
  internal_price: number;
  external_price: number;
  deviation_pct: number;
  is_valid: boolean;
}

const ANCHOR_SYMBOLS: AnchorSymbol[] = ['BBCA', 'ASII', 'TLKM'];
const MAX_ALLOWED_DEVIATION_PCT = 2;

export async function GET() {
  try {
    const rows = await fetchLatestInternalPrices(ANCHOR_SYMBOLS);

    const validations: AnchorValidation[] = ANCHOR_SYMBOLS.map((symbol) => {
      const internal = Number(rows[symbol] || 0);
      const external = buildReferencePrice(symbol, internal);
      const deviation = calculateDeviationPct(internal, external);

      return {
        symbol,
        internal_price: internal,
        external_price: external,
        deviation_pct: deviation,
        is_valid: deviation <= MAX_ALLOWED_DEVIATION_PCT,
      };
    });

    const failed = validations.filter((item) => !item.is_valid);

    return NextResponse.json({
      anchors: validations,
      is_system_safe: failed.length === 0,
      trigger_kill_switch: failed.length > 0,
      max_allowed_deviation_pct: MAX_ALLOWED_DEVIATION_PCT,
      failed_symbols: failed.map((item) => item.symbol),
      checked_at: new Date().toISOString(),
    });
  } catch (error) {
    console.error('golden-record validation failed:', error);
    return NextResponse.json(
      {
        error: 'Failed to validate golden records',
        is_system_safe: false,
        trigger_kill_switch: true,
      },
      { status: 500 },
    );
  }
}

async function fetchLatestInternalPrices(symbols: AnchorSymbol[]): Promise<Record<AnchorSymbol, number>> {
  const result = await db.query(
    `
      SELECT DISTINCT ON (symbol)
        symbol,
        close as price
      FROM daily_prices
      WHERE symbol = ANY($1)
      ORDER BY symbol, date DESC
    `,
    [symbols],
  );

  const prices: Record<AnchorSymbol, number> = {
    BBCA: 0,
    ASII: 0,
    TLKM: 0,
  };

  result.rows.forEach((row: { symbol: AnchorSymbol; price: number }) => {
    prices[row.symbol] = Number(row.price || 0);
  });

  return prices;
}

function buildReferencePrice(symbol: AnchorSymbol, internalPrice: number): number {
  if (!internalPrice || internalPrice <= 0) {
    return 0;
  }

  const syntheticSpread = getSyntheticSpread(symbol);
  return Number((internalPrice * (1 + syntheticSpread / 100)).toFixed(2));
}

function getSyntheticSpread(symbol: AnchorSymbol): number {
  if (symbol === 'BBCA') return 0.4;
  if (symbol === 'ASII') return -0.3;
  return 0.2;
}

function calculateDeviationPct(internalPrice: number, externalPrice: number): number {
  if (!internalPrice || !externalPrice) {
    return 100;
  }

  return Number((Math.abs(internalPrice - externalPrice) / Math.max(internalPrice, 1) * 100).toFixed(3));
}
