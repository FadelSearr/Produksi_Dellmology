'use client';

import { useEffect, useState } from 'react';
import { TrendingUp, TrendingDown, AlertTriangle, Activity } from 'lucide-react';

interface BrokerData {
  broker_id: string;
  net_buy_value: number;
  consistency_score: number;
  is_whale: boolean;
  is_retail: boolean;
  is_anomalous: boolean;
  z_score: number;
}

interface BrokerFlowData {
  symbol: string;
  days: number;
  filter: string;
  brokers: BrokerData[];
  stats: {
    total_brokers: number;
    whales: number;
    retail: number;
    wash_sale_score: number;
  };
  last_updated: string;
}

interface FilterOption {
  value: string;
  label: string;
}

export const FlowEngine = ({ symbol = 'BBCA' }: { symbol?: string }) => {
  const [data, setData] = useState<BrokerFlowData | null>(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(7);
  const [filter, setFilter] = useState('mix');
  const [error, setError] = useState<string | null>(null);

  const filters: FilterOption[] = [
    { value: 'mix', label: '🎭 Mix' },
    { value: 'whale', label: '🐋 Whale' },
    { value: 'retail', label: '👥 Retail' },
    { value: 'smart_money', label: '🧠 Smart Money' },
  ];

  const timelines = [
    { value: 1, label: '1 Day' },
    { value: 7, label: '1 Week' },
    { value: 14, label: '2 Weeks' },
    { value: 21, label: '3 Weeks' },
  ];

  useEffect(() => {
    const fetchBrokerFlow = async () => {
      try {
        setLoading(true);
        const response = await fetch(
          `/api/broker-flow?symbol=${symbol}&days=${days}&filter=${filter}`
        );

        if (!response.ok) {
          throw new Error('Failed to fetch broker flow data');
        }

        const data = await response.json();
        setData(data);
        setError(null);
      } catch (err) {
        console.error('Error fetching broker flow:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchBrokerFlow();
  }, [symbol, days, filter]);

  if (error) {
    return (
      <div className="bg-gray-800/50 border border-red-700 rounded-lg p-6 text-red-400">
        <p>Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">🌊 The Flow Engine</h2>
          <p className="text-sm text-gray-400 mt-1">Broker Flow & Bandarmology Hub</p>
        </div>
      </div>

      {/* Control Bar */}
      <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4 space-y-4">
        <div className="flex flex-col lg:flex-row gap-4">
          {/* Filter Section */}
          <div className="flex-1">
            <label className="text-xs text-gray-400 block mb-2">FILTER</label>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
              {filters.map((f) => (
                <button
                  key={f.value}
                  onClick={() => setFilter(f.value)}
                  className={`px-3 py-2 rounded text-sm transition-colors ${
                    filter === f.value
                      ? 'bg-cyan-500 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          {/* Timeline Section */}
          <div className="flex-1">
            <label className="text-xs text-gray-400 block mb-2">TIMELINE</label>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
              {timelines.map((t) => (
                <button
                  key={t.value}
                  onClick={() => setDays(t.value)}
                  className={`px-3 py-2 rounded text-sm transition-colors ${
                    days === t.value
                      ? 'bg-purple-500 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-gray-800/50 border border-gray-700 rounded-lg p-4 animate-pulse">
              <div className="h-4 bg-gray-700 rounded w-1/3 mb-2"></div>
              <div className="h-3 bg-gray-700 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      ) : data ? (
        <>
          {/* Stats Summary */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-gradient-to-br from-blue-900/40 to-blue-900/20 border border-blue-700/50 rounded-lg p-4">
              <div className="text-xs text-gray-400 mb-2">Total Brokers</div>
              <div className="text-2xl font-bold text-blue-400">{data.stats.total_brokers}</div>
            </div>

            <div className="bg-gradient-to-br from-yellow-900/40 to-yellow-900/20 border border-yellow-700/50 rounded-lg p-4">
              <div className="text-xs text-gray-400 mb-2">🐋 Whales</div>
              <div className="text-2xl font-bold text-yellow-400">{data.stats.whales}</div>
            </div>

            <div className="bg-gradient-to-br from-green-900/40 to-green-900/20 border border-green-700/50 rounded-lg p-4">
              <div className="text-xs text-gray-400 mb-2">👥 Retail</div>
              <div className="text-2xl font-bold text-green-400">{data.stats.retail}</div>
            </div>

            <div className={`bg-gradient-to-br ${data.stats.wash_sale_score > 60 ? 'from-red-900/40 to-red-900/20 border border-red-700/50' : 'from-orange-900/40 to-orange-900/20 border border-orange-700/50'} rounded-lg p-4`}>
              <div className="text-xs text-gray-400 mb-2">⚠️ Wash Sale</div>
              <div className={`text-2xl font-bold ${data.stats.wash_sale_score > 60 ? 'text-red-400' : 'text-orange-400'}`}>
                {data.stats.wash_sale_score.toFixed(0)}%
              </div>
            </div>
          </div>

          {/* Broker List - Deep Broker Flow Table */}
          <div className="bg-gray-800/50 border border-gray-700 rounded-lg overflow-hidden">
            <div className="bg-gray-900/50 border-b border-gray-700 px-6 py-4">
              <h3 className="text-sm font-semibold text-white">Deep Broker Flow Analysis</h3>
            </div>

            <div className="divide-y divide-gray-700">
              {data.brokers.length === 0 ? (
                <div className="px-6 py-8 text-center text-gray-400">
                  No brokers matching current filters
                </div>
              ) : (
                data.brokers.slice(0, 10).map((broker, idx) => (
                  <div key={broker.broker_id} className="px-6 py-4 hover:bg-gray-700/20 transition-colors">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className="text-xs bg-gray-700 text-gray-300 px-2 py-1 rounded">
                          #{idx + 1}
                        </div>
                        <div>
                          <div className="font-semibold text-white">{broker.broker_id}</div>
                          <div className="text-xs text-gray-400">
                            {broker.is_whale && '🐋 Whale • '}
                            {broker.is_retail && '👥 Retail • '}
                            Z-Score: {broker.z_score.toFixed(2)} • 
                            {' '}Consistency: {broker.consistency_score.toFixed(0)}%
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        {broker.net_buy_value > 0 ? (
                          <TrendingUp className="text-green-500" size={18} />
                        ) : (
                          <TrendingDown className="text-red-500" size={18} />
                        )}
                        <div
                          className={`text-right font-semibold ${
                            broker.net_buy_value > 0 ? 'text-green-400' : 'text-red-400'
                          }`}
                        >
                          {broker.net_buy_value > 0 ? '+' : ''}
                          {(broker.net_buy_value / 1e9).toFixed(2)}B
                        </div>
                      </div>
                    </div>

                    {/* Mini Heatmap (daily data) */}
                    <div className="flex gap-1">
                      {broker.daily_heatmap && broker.daily_heatmap.length > 0 ? (
                        (() => {
                          // scale opacity by maximum magnitude present
                          const mags = broker.daily_heatmap.map((v: number) => Math.abs(v));
                          const maxMag = Math.max(...mags, 1);
                          return broker.daily_heatmap.map((val: number, i: number) => {
                            const intensity = Math.min(1, Math.abs(val) / maxMag);
                            return (
                              <div
                                key={i}
                                className="flex-1 h-6 rounded-sm transition-opacity"
                                title={`Day ${i - days + 1}: ${val.toLocaleString()}`}
                                style={{
                                  background: val > 0 ? '#10b981' : '#ef4444',
                                  opacity: 0.2 + 0.8 * intensity,
                                }}
                              ></div>
                            );
                          });
                        })()
                      ) : (
                        // fallback empty boxes when no heatmap data
                        [...Array(days)].map((_, i) => (
                          <div
                            key={i}
                            className="flex-1 h-6 bg-gray-700 rounded-sm opacity-60 hover:opacity-100 transition-opacity"
                            title={`Day ${i - days + 1}`}
                          ></div>
                        ))
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Wash Sale Alert */}
          {data.stats.wash_sale_score > 60 && (
            <div className="bg-red-900/20 border border-red-700/50 rounded-lg p-4 flex gap-3">
              <AlertTriangle className="text-red-500 shrink-0" size={20} />
              <div>
                <h4 className="text-sm font-semibold text-red-300 mb-1">Wash Sale Alert</h4>
                <p className="text-sm text-red-200">
                  High wash sale score ({data.stats.wash_sale_score.toFixed(0)}%) detected. 
                  High volume but low net accumulation suggests potential transaction manipulation.
                </p>
              </div>
            </div>
          )}

          {/* Last Updated */}
          <p className="text-xs text-gray-500 text-right">
            Last updated: {new Date(data.last_updated).toLocaleTimeString()}
          </p>
        </>
      ) : null}
    </div>
  );
};
