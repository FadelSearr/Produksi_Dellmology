package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"time"

	_ "github.com/lib/pq" // PostgreSQL driver
)

// --- Configuration ---
const (
	tokenAPIURL = "http://localhost:3000/api/session"
	databaseURL = "postgresql://admin:password@localhost:5433/dellmology?sslmode=disable"
	// Example: https://api.stockbit.com/v2/broker-summary/BBCA?from=2026-03-01&to=2026-03-01
	brokerSummaryAPIURL = "https://api.stockbit.com/v2/broker-summary/%s?from=%s&to=%s" 
)

// List of stocks to process. In a real system, this would come from a DB or config file.
var targetSymbols = []string{"BBCA", "TLKM", "GOTO", "BBNI"}

// --- Structs ---

type TokenResponse struct {
	Token string `json:"token"`
}

// Represents the structure of the broker summary API response from Stockbit
type BrokerSummaryResponse struct {
	Message string `json:"message"`
	Data    []struct {
		BrokerCode      string `json:"broker_code"`
		BuyValue        int64  `json:"buy_value"`
		SellValue       int64  `json:"sell_value"`
		BuyLot          int64  `json:"buy_lot"`
		SellLot         int64  `json:"sell_lot"`
	} `json:"data"`
}

// --- Main Application ---

func main() {
	log.Println("Starting Dellmology EOD Broker Summary Importer...")

	// 1. Get Auth Token
	token, err := getAuthToken()
	if err != nil {
		log.Fatalf("FATAL: Could not retrieve auth token. Error: %v", err)
	}
	log.Printf("Successfully retrieved auth token: ...%s", token[len(token)-4:])

	// 2. Connect to Database
	db, err := sql.Open("postgres", databaseURL)
	if err != nil {
		log.Fatalf("FATAL: Could not connect to database. Error: %v", err)
	}
	defer db.Close()
	if err = db.Ping(); err != nil {
		log.Fatalf("FATAL: Database ping failed. Error: %v", err)
	}
	log.Println("Successfully connected to the database.")

	// 3. Process each symbol
	today := time.Now().Format("2006-01-02")
	for _, symbol := range targetSymbols {
		log.Printf("Processing symbol: %s", symbol)
		if err := processSymbol(db, token, symbol, today); err != nil {
			log.Printf("ERROR: Failed to process %s: %v", symbol, err)
		} else {
			log.Printf("Successfully processed symbol: %s", symbol)
		}
		time.Sleep(1 * time.Second) // Be nice to the API
	}

	log.Println("EOD Broker Summary Importer finished.")
}

func processSymbol(db *sql.DB, token, symbol, date string) error {
	// 1. Fetch data from API
	url := fmt.Sprintf(brokerSummaryAPIURL, symbol, date, date)
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}
	req.Header.Add("Authorization", "Bearer "+token)

	client := &http.Client{Timeout: 15 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("api request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("api returned non-200 status: %s", resp.Status)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return fmt.Errorf("failed to read response body: %w", err)
	}

	var summary BrokerSummaryResponse
	if err := json.Unmarshal(body, &summary); err != nil {
		return fmt.Errorf("failed to parse json response: %w", err)
	}
	
	if summary.Message != "success" {
		return fmt.Errorf("api indicated failure: %s", summary.Message)
	}
	
	if len(summary.Data) == 0 {
		log.Printf("WARN: No broker summary data returned for %s on %s", symbol, date)
		return nil
	}

	// 2. Insert data into database (using a transaction)
	tx, err := db.Begin()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback() // Rollback on error

	stmt, err := tx.Prepare(`
		INSERT INTO broker_summaries (date, symbol, broker_id, net_buy_value, avg_buy_price, avg_sell_price)
		VALUES ($1, $2, $3, $4, $5, $6)
		ON CONFLICT (date, symbol, broker_id) DO UPDATE
		SET net_buy_value = EXCLUDED.net_buy_value,
			avg_buy_price = EXCLUDED.avg_buy_price,
			avg_sell_price = EXCLUDED.avg_sell_price;
	`)
	if err != nil {
		return fmt.Errorf("failed to prepare statement: %w", err)
	}
	defer stmt.Close()

	for _, item := range summary.Data {
		netBuy := item.BuyValue - item.SellValue
		
		var avgBuy, avgSell float64
		if item.BuyLot > 0 {
			avgBuy = float64(item.BuyValue) / float64(item.BuyLot) / 100
		}
		if item.SellLot > 0 {
			avgSell = float64(item.SellValue) / float64(item.SellLot) / 100
		}

		_, err := stmt.Exec(date, symbol, item.BrokerCode, netBuy, avgBuy, avgSell)
		if err != nil {
			return fmt.Errorf("failed to execute statement for broker %s: %w", item.BrokerCode, err)
		}
	}

	return tx.Commit()
}

// getAuthToken fetches the bearer token from the web API
func getAuthToken() (string, error) {
	client := &http.Client{Timeout: 10 * time.Second}
	req, err := http.NewRequest("GET", tokenAPIURL, nil)
	if err != nil {
		return "", fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("failed to fetch token from api: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("api returned non-200 status: %s", resp.Status)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("failed to read response body: %w", err)
	}

	var tokenResp TokenResponse
	if err := json.Unmarshal(body, &tokenResp); err != nil {
		return "", fmt.Errorf("failed to parse json response: %w", err)
	}

	if tokenResp.Token == "" {
		return "", fmt.Errorf("token not found in api response")
	}

	return tokenResp.Token, nil
}
