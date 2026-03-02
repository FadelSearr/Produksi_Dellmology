'use client';

import { useEffect, useState } from 'react';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';

// Import all section components
import { Section0_CommandBar } from '@/components/sections/Section0_CommandBar';
import { Section1_MarketIntelligence } from '@/components/sections/Section1_MarketIntelligence';
import { Section2_BrokerFlow } from '@/components/sections/Section2_BrokerFlow';
import { Section3_NeuralNarrative } from '@/components/sections/Section3_NeuralNarrative';
import { Section4_RiskDock } from '@/components/sections/Section4_RiskDock';
import { Section5_Performance } from '@/components/sections/Section5_Performance';

interface ProcessedTrade {
  id: string;
  symbol: string;
  price: number;
  volume: number;
  timestamp: string;
  type: 'HAKA' | 'HAKI' | 'NORMAL';
}

const MAX_TRADES_IN_LIST = 50;
const STREAM_URL = 'http://localhost:8080/stream';

/**
 * Main Dashboard - Dellmology Pro
 * Combines all 6 sections (0-5) into a unified vertical scroll layout
 */
export default function Home() {
  const [symbol, setSymbol] = useState('BBCA');
  const [timeframe, setTimeframe] = useState<'5m' | '15m' | '1h' | '4h' | '1d'>('1h');
  const [trades, setTrades] = useState<ProcessedTrade[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [brokerData, setBrokerData] = useState<any[]>([]);
  const [isLoadingTrades, setIsLoadingTrades] = useState(false);

  // System health state
  const [systemHealth, setSystemHealth] = useState({
    sse: false,
    db: true,
    shield: true,
  });

  // Fetch trades via SSE
  useEffect(() => {
    setIsLoadingTrades(true);
    const eventSource = new EventSource(STREAM_URL);

    eventSource.onopen = () => {
      console.log('✓ SSE connection established');
      setIsConnected(true);
      setSystemHealth((prev) => ({ ...prev, sse: true }));
    };

    eventSource.onmessage = (event) => {
      try {
        const trade = JSON.parse(event.data) as ProcessedTrade;
        setTrades((prevTrades) => {
          const newTrades = [trade, ...prevTrades];
          return newTrades.slice(0, MAX_TRADES_IN_LIST);
        });
        setIsLoadingTrades(false);
      } catch (error) {
        console.error('Failed to parse trade data:', error);
      }
    };

    eventSource.onerror = (err) => {
      console.error('SSE connection error:', err);
      setIsConnected(false);
      setSystemHealth((prev) => ({ ...prev, sse: false }));
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, []);

  // Fetch broker flow data
  useEffect(() => {
    const loadBrokerData = async () => {
      try {
        const res = await fetch(`/api/broker-flow?symbol=${symbol}`);
        if (res.ok) {
          const json = await res.json();
          setBrokerData(json.brokers || []);
        }
      } catch (e) {
        console.error('Failed to fetch broker flow:', e);
      }
    };
    loadBrokerData();
    // Poll every 60 seconds
    const interval = setInterval(loadBrokerData, 60000);
    return () => clearInterval(interval);
  }, [symbol]);

  return (
    <div className="bg-gray-900 text-white min-h-screen">
      <ErrorBoundary>
        {/* SECTION 0: Command Bar (Sticky) */}
        <Section0_CommandBar
          onSymbolChange={setSymbol}
          marketRegime="BULLISH"
          volatility="HIGH"
          systemHealth={systemHealth}
          rateLimitUsage={65}
        />

        {/* Main Content */}
        <main className="pt-4">
          <div className="max-w-screen-2xl mx-auto px-4 space-y-8">
            {/* SECTION 1: Market Intelligence Canvas */}
            <ErrorBoundary>
              <Section1_MarketIntelligence
                symbol={symbol}
                isLoading={isLoadingTrades}
                timeframe={timeframe}
                onTimeframeChange={(tf: string) => setTimeframe(tf as any)}
                unifiedPowerScore={75}
              />
            </ErrorBoundary>

            {/* SECTION 2: Broker Flow Engine */}
            <ErrorBoundary>
              <Section2_BrokerFlow symbol={symbol} brokerData={brokerData} />
            </ErrorBoundary>

            {/* SECTION 3: Neural Narrative Hub */}
            <ErrorBoundary>
              <Section3_NeuralNarrative symbol={symbol} />
            </ErrorBoundary>

            {/* SECTION 4: Risk & Tactical Dock */}
            <ErrorBoundary>
              <Section4_RiskDock
                symbol={symbol}
                trades={trades}
                unrealizedPnL={2500000}
                maxLot={250}
                stopLossPercent={2.5}
                volatilityLevel="HIGH"
              />
            </ErrorBoundary>

            {/* SECTION 5: Performance & Infrastructure Lab */}
            <ErrorBoundary>
              <Section5_Performance
                symbol={symbol}
                systemStatus={{
                  database: systemHealth.db,
                  streamer: systemHealth.sse,
                  dataSync: true,
                }}
                modelMetrics={{
                  tradesPerMin: trades.length > 0 ? Math.round(trades.length * 3) : 342,
                  latencyMs: 45,
                  uptime: '99.8%',
                }}
              />
            </ErrorBoundary>

            {/* Footer Spacer */}
            <div className="h-16" />
          </div>
        </main>
      </ErrorBoundary>
    </div>
  );
}
