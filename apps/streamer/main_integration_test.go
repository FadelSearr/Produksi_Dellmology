//go:build integration
// +build integration

package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"net/url"
	"testing"
	"time"

	"github.com/DATA-DOG/go-sqlmock"
	"github.com/gorilla/websocket"
)

func TestMessageLoop_InsertsTrade(t *testing.T) {
	// setup sqlmock and assign to package-level db
	mockDB, mock, err := sqlmock.New()
	if err != nil {
		t.Fatalf("failed to open sqlmock: %v", err)
	}
	defer mockDB.Close()
	db = mockDB

	// prepare sseBroker to avoid nil deref
	sseBroker = &Broker{messages: make(chan []byte, 4), newClients: make(chan chan []byte), defunctClients: make(chan chan []byte), clients: make(map[chan []byte]bool)}

	// prepare messageQueue and worker
	messageQueue = make(chan []byte, 10)
	go messageWorker(1)

	// Expect DB insert for the processed trade. Timestamp will be AnyArg.
	mock.ExpectExec("INSERT INTO trades").WithArgs("TST", 100.0, int64(10), "NORMAL", sqlmock.AnyArg()).WillReturnResult(sqlmock.NewResult(1, 1))

	// start a test websocket server that upgrades and sends one trade frame
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		upgrader := websocket.Upgrader{}
		conn, err := upgrader.Upgrade(w, r, nil)
		if err != nil {
			t.Fatalf("upgrade failed: %v", err)
			return
		}
		defer conn.Close()

		trade := map[string]interface{}{"s": "TST", "p": 100.0, "v": 10, "dt": time.Now().Unix()}
		payload, _ := json.Marshal(trade)
		frame := map[string]interface{}{"t": "trade", "d": json.RawMessage(payload)}
		frameBytes, _ := json.Marshal(frame)

		if err := conn.WriteMessage(websocket.TextMessage, frameBytes); err != nil {
			t.Fatalf("failed to write message: %v", err)
		}
		// keep connection open briefly
		time.Sleep(100 * time.Millisecond)
	}))
	defer srv.Close()

	// build ws url
	u, _ := url.Parse(srv.URL)
	wsURL := "ws://" + u.Host + "/"

	conn, _, err := websocket.DefaultDialer.Dial(wsURL, nil)
	if err != nil {
		t.Fatalf("dial failed: %v", err)
	}
	defer conn.Close()

	// run messageLoop (reads one message then queues it)
	go messageLoop(conn)

	// wait for processing
	time.Sleep(300 * time.Millisecond)

	if err := mock.ExpectationsWereMet(); err != nil {
		t.Fatalf("unmet expectations: %v", err)
	}
}
