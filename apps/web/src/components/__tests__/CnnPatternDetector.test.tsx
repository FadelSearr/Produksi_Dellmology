import { render, screen } from '@testing-library/react';
import { CnnPatternDetector } from '../CnnPatternDetector';

global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () =>
      Promise.resolve({
        detected_patterns: [],
        confidences: { high: 0, medium: 0, low: 0 },
      }),
  } as any)
) as jest.Mock;

describe('CnnPatternDetector', () => {
  it('renders title', async () => {
    render(<CnnPatternDetector symbol="TEST" />);
    expect(await screen.findByText('Detected Patterns')).toBeInTheDocument();
  });
});