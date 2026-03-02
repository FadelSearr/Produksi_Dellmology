'use client';

import React, { useState } from 'react';
import { Brain, Filter } from 'lucide-react';
import { Card } from '@/components/common/Card';
import { AIScreener } from '@/components/intelligence/AIScreener';
import { AINarrativeDisplay } from '@/components/intelligence/AINarrativeDisplay';

interface Section3Props {
  symbol: string;
  aiNarrative?: string;
  isLoading?: boolean;
}

/**
 * Section 3: Neural Narrative Hub (Intelligence & Screener)
 * - AI Screener (Daytrade/Swing modes)
 * - Custom range filters
 * - AI Narrative Terminal
 * - Retail sentiment divergence
 * - Multi-model voting system
 */
export const Section3_NeuralNarrative: React.FC<Section3Props> = ({
  symbol,
  aiNarrative,
  isLoading = false,
}) => {
  const [screenerMode, setScreenerMode] = useState<'DAYTRADE' | 'SWING' | 'CUSTOM'>('DAYTRADE');
  const [priceRange, setPriceRange] = useState({ min: 100, max: 10000 });

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <Brain className="w-6 h-6 text-purple-400" />
        <h2 className="text-2xl font-bold text-white">🧠 Neural Narrative Hub</h2>
      </div>

      {/* Screener Controls */}
      <Card className="space-y-4" noPadding>
        <div className="p-4 border-b border-gray-700">
          <div className="text-xs font-semibold text-gray-400 mb-3 uppercase tracking-wider">AI Screener Configuration</div>

          {/* Mode Selector */}
          <div className="space-y-3">
            <div className="flex gap-2">
              {(['DAYTRADE', 'SWING', 'CUSTOM'] as const).map((mode) => (
                <button
                  key={mode}
                  onClick={() => setScreenerMode(mode)}
                  className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                    mode === screenerMode
                      ? 'bg-purple-600 text-white shadow-lg shadow-purple-600/50'
                      : 'bg-gray-700/30 text-gray-400 hover:bg-gray-700/50'
                  }`}
                >
                  {mode === 'DAYTRADE' ? '⚡ Daytrade' : mode === 'SWING' ? '📊 Swing' : '🎨 Custom'}
                </button>
              ))}
            </div>

            {/* Custom Range Filter */}
            {screenerMode === 'CUSTOM' && (
              <div className="pt-3 border-t border-gray-700">
                <label className="text-xs text-gray-400">Price Range Filter (IDR)</label>
                <div className="flex gap-2 mt-2">
                  <input
                    type="number"
                    value={priceRange.min}
                    onChange={(e) => setPriceRange({ ...priceRange, min: parseInt(e.target.value) })}
                    className="flex-1 px-3 py-1 bg-gray-700/50 border border-gray-600 rounded text-white text-sm"
                    placeholder="Min"
                  />
                  <span className="text-gray-500">-</span>
                  <input
                    type="number"
                    value={priceRange.max}
                    onChange={(e) => setPriceRange({ ...priceRange, max: parseInt(e.target.value) })}
                    className="flex-1 px-3 py-1 bg-gray-700/50 border border-gray-600 rounded text-white text-sm"
                    placeholder="Max"
                  />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Screener Results */}
        <div className="p-4">
          {screenerMode !== 'CUSTOM' && (
            <AIScreener mode={screenerMode} />
          )}
          {screenerMode === 'CUSTOM' && (
            <div className="text-center py-8 text-gray-400">
              <p>Custom screener with filters: Rp {priceRange.min.toLocaleString()} - Rp {priceRange.max.toLocaleString()}</p>
              <p className="text-sm mt-2">Loading custom results...</p>
            </div>
          )}
        </div>
      </Card>

      {/* AI Narrative Terminal */}
      <Card title="💬 AI Narrative Terminal (Gemini)" subtitle="Strategic SWOT analysis with confidence scores">
        <div className="space-y-4">
          <AINarrativeDisplay symbol={symbol} type="swot" autoRefresh={true} />
          <div className="pt-4 border-t border-gray-700">
            <p className="text-xs text-gray-400">
              💡 Tip: Each narrative includes a bearish counter-case to avoid confirmation bias.
            </p>
          </div>
        </div>
      </Card>

      {/* Retail Sentiment */}
      <Card title="👥 Retail Sentiment Divergence" subtitle="Trader enthusiasm vs Whale accumulation">
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-xs text-gray-400 mb-1">Retail Sentiment</div>
              <div className="text-2xl font-bold text-green-400">+78%</div>
              <div className="text-xs text-gray-500">Very Bullish</div>
            </div>
            <div>
              <div className="text-xs text-gray-400 mb-1">Whale Confidence</div>
              <div className="text-2xl font-bold text-orange-400">+35%</div>
              <div className="text-xs text-gray-500">Moderate</div>
            </div>
          </div>
          <div className="bg-yellow-900/20 border border-yellow-700 rounded p-3 text-xs text-yellow-200">
            ⚠️ DIVERGENCE DETECTED: Retail euphoria but whale accumulation slowing. Risk of distribution incoming.
          </div>
        </div>
      </Card>
    </div>
  );
};
