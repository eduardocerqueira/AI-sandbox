package main

import (
	"log"
	"net/http"
	"os"
	"strings"
)

func main() {
	token := strings.TrimSpace(os.Getenv("HF_TOKEN"))
	if token == "" {
		log.Fatal("HF_TOKEN is not set. Export it before starting the server.")
	}

	port := strings.TrimSpace(os.Getenv("PORT"))
	if port == "" {
		port = "8080"
	}
	model := strings.TrimSpace(os.Getenv("HF_MODEL"))

	client := newSentimentClient(token, model)
	srv := newAPIServer(client)
	addr := ":" + port

	log.Printf("hf-sentiment-server listening on http://127.0.0.1%s", addr)
	log.Printf("model: %s", client.modelID())
	log.Printf("POST /v1/sentiment  body: {\"text\":\"...\"}")
	if err := http.ListenAndServe(addr, srv.routes()); err != nil {
		log.Fatal(err)
	}
}
