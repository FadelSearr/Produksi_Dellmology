'use client';

import React from 'react';
import { AlertTriangle, TrendingDown } from 'lucide-react';

interface ExitWhaleTableProps {
  symbol: string;
}

/**
 * Exit Whale detection table showing institutional distribution patterns
 */
export const ExitWhaleTable: React.FC<ExitWhaleTableProps> = ({ symbol }) => {
  // Mock data for whale exit detection
  const whaleExits = [
    {
      id: 1,
      broker: 'PT Mandiri Sekuritas',
      avgPrice: 15250,
      volume: 500000,
      netChange: -350000,
      confidence: 0.92,
      pattern: 'Gradual Distribution',
    },
    {
      id: 2,
      broker: 'PT Mirae Asset',
      avgPrice: 15180,
      volume: 320000,
      netChange: -280000,
      confidence: 0.85,
      pattern: 'Block Accumulation',
    },
    {
      id: 3,
      broker: 'PT UOB Kay Hian',
      avgPrice: 15100,
      volume: 210000,
      netChange: -150000,
      confidence: 0.78,
      pattern: 'Intraday Dump',
    },
  ];

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-700">
            <th className="text-left px-3 py-2 text-xs font-semibold text-gray-400">BROKER</th>
            <th className="text-right px-3 py-2 text-xs font-semibold text-gray-400">AVG PRICE</th>
            <th className="text-right px-3 py-2 text-xs font-semibold text-gray-400">VOLUME</th>
            <th className="text-right px-3 py-2 text-xs font-semibold text-gray-400">NET CHANGE</th>
            <th className="text-center px-3 py-2 text-xs font-semibold text-gray-400">CONFIDENCE</th>
            <th className="text-left px-3 py-2 text-xs font-semibold text-gray-400">PATTERN</th>
          </tr>
        </thead>
        <tbody>
          {whaleExits.map((exit, idx) => (
            <tr key={exit.id} className="border-b border-gray-700/50 hover:bg-gray-800/30 transition-colors">
              <td className="px-3 py-2">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-red-500" />
                  <span className="text-gray-300 font-semibold">{exit.broker}</span>
                </div>
              </td>
              <td className="text-right px-3 py-2 font-mono text-cyan-400">Rp {exit.avgPrice.toLocaleString()}</td>
              <td className="text-right px-3 py-2 font-mono text-gray-300">{(exit.volume / 1000).toFixed(0)}K</td>
              <td className="text-right px-3 py-2">
                <span className="font-mono text-red-400">{(exit.netChange / 1000).toFixed(0)}K</span>
              </td>
              <td className="text-center px-3 py-2">
                <div className="inline-flex items-center gap-1">
                  <div className="w-16 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-linear-to-r from-orange-500 to-red-500"
                      style={{ width: `${exit.confidence * 100}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-400">{(exit.confidence * 100).toFixed(0)}%</span>
                </div>
              </td>
              <td className="px-3 py-2 text-gray-400 text-xs">{exit.pattern}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Alert */}
      <div className="mt-3 p-3 bg-red-900/20 border border-red-700/50 rounded text-xs text-red-200 flex items-start gap-2">
        <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
        <div>
          <p className="font-semibold mb-1">⚠️ Exit Whale Activity Detected</p>
          <p>Institutional investors showing signs of distribution. Monitor for potential pullback.</p>
        </div>
      </div>
    </div>
  );
};
