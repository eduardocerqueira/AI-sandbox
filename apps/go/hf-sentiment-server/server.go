package main

import (
	"encoding/json"
	"net/http"
	"strings"
)

type classifyRequest struct {
	Text string `json:"text"`
}

type classifyResponse struct {
	Model  string           `json:"model"`
	Text   string           `json:"text"`
	Labels []sentimentLabel `json:"labels"`
}

type apiServer struct {
	classifier classifier
}

func newAPIServer(c classifier) *apiServer {
	return &apiServer{classifier: c}
}

func (s *apiServer) routes() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /health", s.handleHealth)
	mux.HandleFunc("POST /v1/sentiment", s.handleSentiment)
	return mux
}

func (s *apiServer) handleHealth(w http.ResponseWriter, _ *http.Request) {
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

func (s *apiServer) handleSentiment(w http.ResponseWriter, r *http.Request) {
	var req classifyRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid JSON body"})
		return
	}
	text := strings.TrimSpace(req.Text)
	if text == "" {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "text is required"})
		return
	}

	labels, err := s.classifier.classify(text)
	if err != nil {
		writeJSON(w, http.StatusBadGateway, map[string]string{"error": err.Error()})
		return
	}

	writeJSON(w, http.StatusOK, classifyResponse{
		Model:  s.classifier.modelID(),
		Text:   text,
		Labels: labels,
	})
}

func writeJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(payload)
}
