package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"sync"
	"time"

	"github.com/gorilla/websocket"
	_ "github.com/lib/pq" // PostgreSQL driver
)

// --- Configuration ---
const (
	tokenAPIURL      = "http://localhost:3000/api/session"
	websocketURL     = "wss://stream.stockbit.com/stream"
	databaseURL      = "postgresql://admin:password@localhost:5433/dellmology?sslmode=disable"
	httpListenAddr   = ":8080"
	reconnectWait    = 5 * time.Second
)

// --- Structs ---

// TokenResponse matches the JSON structure of the /api/session endpoint
type TokenResponse struct {
	Token string `json:"token"`
}

// WebSocketMessage defines the generic structure of incoming messages
type WebSocketMessage struct {
	Type string          `json:"t"`    // e.g., "trade", "quote"
	Data json.RawMessage `json:"d"`
}

// TradeData represents a single trade event
type TradeData struct {
	Symbol    string  `json:"s"`
	Price     float64 `json:"p"`
	Volume    int64   `json:"v"`
	Timestamp int64   `json:"dt"` // Unix timestamp
}

// QuoteData represents a bid/offer update
type QuoteData struct {
	Symbol    string  `json:"s"`
	Bid       float64 `json:"b"`
	Offer     float64 `json:"o"`
	Timestamp int64   `json:"dt"`
}

// ProcessedTrade is the enriched data we send to the frontend and DB
type ProcessedTrade struct {
	Symbol    string    `json:"symbol"`
	Price     float64   `json:"price"`
	Volume    int64     `json:"volume"`
	TradeType string    `json:"trade_type"` // "HAKA", "HAKI", or "NORMAL"
	Timestamp time.Time `json:"timestamp"`
}

// --- Global State ---
var (
	db           *sql.DB
	latestQuotes = make(map[string]QuoteData)
	quotesMutex  = &sync.RWMutex{}
	sseBroker    *Broker
)

// --- SSE Broker ---

// Broker manages SSE client connections and broadcasts messages.
type Broker struct {
	clients      map[chan []byte]bool
	newClients   chan chan []byte
	defunctClients chan chan []byte
	messages     chan []byte
	mutex        sync.Mutex
}

func (b *Broker) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")
	
	flusher, ok := w.(http.Flusher)
	if !ok {
		http.Error(w, "Streaming unsupported!", http.StatusInternalServerError)
		return
	}

	messageChan := make(chan []byte)
	b.newClients <- messageChan
	defer func() {
		b.defunctClients <- messageChan
	}()

	ctx := r.Context()
	for {
		select {
		case msg := <-messageChan:
			fmt.Fprintf(w, "data: %s\n\n", msg)
			flusher.Flush()
		case <-ctx.Done():
			return
		}
	}
}

func (b *Broker) run() {
	for {
		select {
		case s := <-b.newClients:
			b.mutex.Lock()
			b.clients[s] = true
			b.mutex.Unlock()
			log.Println("SSE client connected.")
		case s := <-b.defunctClients:
			b.mutex.Lock()
			delete(b.clients, s)
			b.mutex.Unlock()
			log.Println("SSE client disconnected.")
		case msg := <-b.messages:
			b.mutex.Lock()
			for s := range b.clients {
				s <- msg
			}
			b.mutex.Unlock()
		}
	}
}

func newBroker() *Broker {
	return &Broker{
		clients:      make(map[chan []byte]bool),
		newClients:   make(chan (chan []byte)),
		defunctClients: make(chan (chan []byte)),
		messages:     make(chan []byte, 100), // Buffered channel
	}
}

// --- Main Application ---

func main() {
	var err error
	log.Println("Initializing Dellmology Pro Data Streamer...")

	// Initialize SSE Broker
	sseBroker = newBroker()
	go sseBroker.run()

	// Initialize Database
	db, err = initDB()
	if err != nil {
		log.Fatalf("FATAL: Could not connect to database. Error: %v", err)
	}
	defer db.Close()
	log.Println("Successfully connected to the database.")

	// Start HTTP server for SSE
	go startHTTPServer()

	// Main application loop
	runStreamer()
}

func runStreamer() {
	for {
		token, err := getAuthToken()
		if err != nil {
			log.Printf("ERROR: Could not retrieve auth token: %v. Retrying in %v...", err, reconnectWait)
			time.Sleep(reconnectWait)
			continue
		}
		log.Printf("Successfully retrieved auth token: ...%s", token[len(token)-4:])

		conn, err := connectWebSocket(token)
		if err != nil {
			log.Printf("ERROR: Failed to connect to WebSocket: %v. Retrying in %v...", err, reconnectWait)
			time.Sleep(reconnectWait)
			continue
		}

		log.Println("Successfully connected to WebSocket. Listening for messages...")
		messageLoop(conn) // This loop will run until a disconnect
		
		conn.Close()
		log.Println("WebSocket disconnected. Attempting to reconnect...")
		time.Sleep(reconnectWait)
	}
}

func messageLoop(conn *websocket.Conn) {
	for {
		_, message, err := conn.ReadMessage()
		if err != nil {
			log.Printf("ERROR: Failed to read message: %v", err)
			return // Exit to trigger reconnection
		}
		go processMessage(message)
	}
}

func processMessage(rawMsg []byte) {
	var msg WebSocketMessage
	if err := json.Unmarshal(rawMsg, &msg); err != nil {
		log.Printf("WARN: Failed to parse generic websocket message: %v", err)
		return
	}

	switch msg.Type {
	case "trade":
		var trade TradeData
		if err := json.Unmarshal(msg.Data, &trade); err != nil {
			log.Printf("WARN: Failed to parse trade data: %v", err)
			return
		}
		
		quotesMutex.RLock()
		quote, ok := latestQuotes[trade.Symbol]
		quotesMutex.RUnlock()

		if !ok {
			return // Cannot determine HAKA/HAKI without a quote
		}

		tradeType := "NORMAL"
		if trade.Price >= quote.Offer {
			tradeType = "HAKA" // Aggressive Buy
		} else if trade.Price <= quote.Bid {
			tradeType = "HAKI" // Aggressive Sell
		}
		
		processed := ProcessedTrade{
			Symbol:    trade.Symbol,
			Price:     trade.Price,
			Volume:    trade.Volume,
			TradeType: tradeType,
			Timestamp: time.Unix(trade.Timestamp, 0),
		}

		// Insert into DB
		if err := insertTrade(processed); err != nil {
			log.Printf("ERROR: Failed to insert trade into DB: %v", err)
		}

		// Broadcast to SSE clients
		jsonData, err := json.Marshal(processed)
		if err == nil {
			sseBroker.messages <- jsonData
		}

	case "quote":
		var quote QuoteData
		if err := json.Unmarshal(msg.Data, &quote); err != nil {
			log.Printf("WARN: Failed to parse quote data: %v", err)
			return
		}

		quotesMutex.Lock()
		latestQuotes[quote.Symbol] = quote
		quotesMutex.Unlock()
	}
}

// --- Database Functions ---

func initDB() (*sql.DB, error) {
	d, err := sql.Open("postgres", databaseURL)
	if err != nil {
		return nil, err
	}
	if err = d.Ping(); err != nil {
		return nil, err
	}
	d.SetMaxOpenConns(10)
	d.SetMaxIdleConns(5)
	d.SetConnMaxLifetime(5 * time.Minute)
	return d, nil
}

func insertTrade(t ProcessedTrade) error {
	query := `
		INSERT INTO trades (symbol, price, volume, trade_type, timestamp)
		VALUES ($1, $2, $3, $4, $5)
	`
	_, err := db.Exec(query, t.Symbol, t.Price, t.Volume, t.TradeType, t.Timestamp)
	return err
}


// --- HTTP & WebSocket Functions ---

func startHTTPServer() {
	mux := http.NewServeMux()
	mux.Handle("/stream", sseBroker)
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		fmt.Fprintln(w, "OK")
	})

	log.Printf("SSE and Health server listening on %s", httpListenAddr)
	if err := http.ListenAndServe(httpListenAddr, mux); err != nil {
		log.Fatalf("FATAL: HTTP server failed: %v", err)
	}
}

func connectWebSocket(token string) (*websocket.Conn, error) {
	headers := http.Header{}
	headers.Add("Authorization", "Bearer "+token)

	conn, _, err := websocket.DefaultDialer.Dial(websocketURL, headers)
	if err != nil {
		return nil, fmt.Errorf("failed to dial websocket: %w", err)
	}
	return conn, nil
}

func getAuthToken() (string, error) {
	client := &http.Client{
		Timeout: 10 * time.Second,
	}
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
		body, _ := io.ReadAll(resp.Body)
		return "", fmt.Errorf("api returned non-200 status: %s - %s", resp.Status, string(body))
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("failed to read response body: %w", err)
	}

	var tokenResp TokenResponse
	if err := json.Unmarshal(body, &tokenResp); err != nil {
		return "", fmt.Errorf("failed to parse json response: %w - %s", err, string(body))
	}

	if tokenResp.Token == "" {
		return "", fmt.Errorf("token not found in api response")
	}

	return tokenResp.Token, nil
}
