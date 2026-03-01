// Broker Flow Analysis and HAKA/HAKI Detection
package analysis

import (
	"log"
)

// AnalyzeBrokerFlow analyzes broker trading patterns
func AnalyzeBrokerFlow(symbol string, days int) map[string]interface{} {
	log.Printf("Analyzing broker flow for %s (last %d days)", symbol, days)
	return map[string]interface{}{
		"symbol": symbol,
		"status": "analyzing",
	}
}

// DetectHAKAHAKI detects aggressive buy (HAKA) and sell (HAKI) trades
func DetectHAKAHAKI(price float64, bid float64, offer float64) string {
	if price == offer {
		return "HAKA" // Aggressive Buy at Ask
	} else if price == bid {
		return "HAKI" // Aggressive Sell at Bid
	}
	return "NEUTRAL"
}

// CalculateZScore calculates Z-Score for anomaly detection
func CalculateZScore(value float64, mean float64, stdDev float64) float64 {
	if stdDev == 0 {
		return 0
	}
	return (value - mean) / stdDev
}

// AnalyzeWalePattern identifies whale (institutional) activity
func AnalyzeWalePattern(volume int64, avgVolume int64, threshold float64) bool {
	if avgVolume == 0 {
		return false
	}
	ratio := float64(volume) / float64(avgVolume)
	return ratio > threshold
}
