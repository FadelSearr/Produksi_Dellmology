import { render, screen, fireEvent } from '@testing-library/react';
import { OrderFlowHeatmap } from '../OrderFlowHeatmap';

// Mock fetch
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () =>
      Promise.resolve({
        heatmap: { prices: [], bidVolumes: [], askVolumes: [], netVolumes: [], bidAskRatios: [], intensities: [] },
        marketDepth: null,
        anomalies: [],
      }),
  } as any)
) as jest.Mock;

describe('OrderFlowHeatmap Component', () => {
  it('renders header and toggle', async () => {
    render(<OrderFlowHeatmap symbol="TEST" />);

    expect(await screen.findByText('Market Depth Heatmap')).toBeInTheDocument();
    expect(screen.getByText('1‑min Aggregated')).toBeInTheDocument();
  });

  it('toggle switches aggregate state', async () => {
    render(<OrderFlowHeatmap symbol="TEST" />);
    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).not.toBeChecked();
    fireEvent.click(checkbox);
    expect(checkbox).toBeChecked();
  });
});
