// Entry point for Broker Importer
package main

import (
	"log"
	"os"
)

func main() {
	databaseURL := os.Getenv("DATABASE_URL")
	if databaseURL == "" {
		databaseURL = "postgresql://admin:password@localhost:5433/dellmology?sslmode=disable"
	}

	log.Println("🚀 Starting Broker Importer...")

	// Create storage
	storage, err := importer.NewStorageDB(databaseURL)
	if err != nil {
		log.Fatalf("Failed to create storage: %v", err)
	}
	defer storage.Close()

	log.Println("✅ Broker Importer initialized successfully")
	log.Println("Ready to import broker data...")

}
