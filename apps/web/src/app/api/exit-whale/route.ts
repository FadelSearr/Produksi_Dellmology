import { NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { sourceMeta } from '@/lib/source-adapter';

export const dynamic = 'force-dynamic';

export async function GET(request: Request) {
  const startedAt = Date.now();
  try {
    const { searchParams } = new URL(request.url);
    const symbol = String(searchParams.get('symbol') || '').toUpperCase();
    const requestedDays = Number.parseInt(searchParams.get('days') || '7', 10);
    const days = Number.isFinite(requestedDays) ? Math.min(90, Math.max(1, requestedDays)) : 7;

    const query = `
      SELECT symbol, broker_id, net_value, z_score, note, time
      FROM exit_whale_events
      WHERE ($1 = '' OR symbol = $1)
        AND time >= NOW() - $2::interval
      ORDER BY time DESC
    `;
    const result = await db.query(query, [symbol, `${days} days`]);

    const events = (result.rows || []).map((row) => ({
      ...row,
      net_value: Number(row.net_value || 0),
      z_score: Number(row.z_score || 0),
    }));

    const strongEvents = events.filter((event) =>
      Number(event.net_value) < 0 && (Number(event.z_score) <= -1.5 || /distribution|exit|liquidity|hunt|sell/i.test(String(event.note || ''))),
    );

    const netDistributionValue = Math.abs(
      strongEvents.reduce((sum, event) => sum + Math.min(0, Number(event.net_value || 0)), 0),
    );

    const warning = strongEvents.length >= 2 && netDistributionValue >= 20_000_000_000;

    return NextResponse.json({
      symbol,
      days,
      events,
      summary: {
        event_count: events.length,
        strong_event_count: strongEvents.length,
        net_distribution_value: netDistributionValue,
        warning,
      },
      degraded: false,
      reason: null,
      data_source: sourceMeta({
        provider: 'PRIMARY_DB',
        degraded: false,
        reason: null,
        fallbackDelayMinutes: 0,
        diagnostics: {
          primary_latency_ms: Math.max(0, Date.now() - startedAt),
          fallback_latency_ms: null,
          primary_error: null,
          selected_source: 'PRIMARY_DB',
          checked_at: new Date().toISOString(),
        },
      }),
    });
  } catch (err) {
    console.error('Error fetching exit whale events', err);
    return NextResponse.json({
      events: [],
      summary: {
        event_count: 0,
        strong_event_count: 0,
        net_distribution_value: 0,
        warning: false,
      },
      degraded: true,
      reason: 'failed to fetch exit whale events',
      data_source: sourceMeta({
        provider: 'FALLBACK_EMPTY',
        degraded: true,
        reason: 'failed to fetch exit whale events',
        fallbackDelayMinutes: 15,
        diagnostics: {
          primary_latency_ms: Math.max(0, Date.now() - startedAt),
          fallback_latency_ms: null,
          primary_error: err instanceof Error ? err.message : 'unknown error',
          selected_source: 'FALLBACK_EMPTY',
          checked_at: new Date().toISOString(),
        },
      }),
    });
  }
}
