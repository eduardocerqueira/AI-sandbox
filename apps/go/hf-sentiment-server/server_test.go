package main

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

type mockClassifier struct {
	model  string
	labels []sentimentLabel
	err    error
	last   string
}

func (m *mockClassifier) modelID() string {
	if m.model != "" {
		return m.model
	}
	return defaultModel
}

func (m *mockClassifier) classify(text string) ([]sentimentLabel, error) {
	m.last = text
	if m.err != nil {
		return nil, m.err
	}
	return m.labels, nil
}

func TestHandleHealth(t *testing.T) {
	s := newAPIServer(&mockClassifier{})
	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	rec := httptest.NewRecorder()
	s.handleHealth(rec, req)
	if rec.Code != http.StatusOK {
		t.Fatalf("status %d", rec.Code)
	}
}

func TestHandleSentiment_emptyText(t *testing.T) {
	s := newAPIServer(&mockClassifier{})
	body := bytes.NewBufferString(`{"text":""}`)
	req := httptest.NewRequest(http.MethodPost, "/v1/sentiment", body)
	rec := httptest.NewRecorder()
	s.handleSentiment(rec, req)
	if rec.Code != http.StatusBadRequest {
		t.Fatalf("status %d body %s", rec.Code, rec.Body.String())
	}
}

func TestHandleSentiment_success(t *testing.T) {
	mock := &mockClassifier{
		labels: []sentimentLabel{{Label: "POSITIVE", Score: 0.99}},
	}
	s := newAPIServer(mock)
	body := bytes.NewBufferString(`{"text":"Go is great"}`)
	req := httptest.NewRequest(http.MethodPost, "/v1/sentiment", body)
	rec := httptest.NewRecorder()
	s.handleSentiment(rec, req)
	if rec.Code != http.StatusOK {
		t.Fatalf("status %d body %s", rec.Code, rec.Body.String())
	}
	var resp classifyResponse
	if err := json.NewDecoder(rec.Body).Decode(&resp); err != nil {
		t.Fatal(err)
	}
	if resp.Text != "Go is great" || resp.Labels[0].Label != "POSITIVE" {
		t.Fatalf("unexpected response: %+v", resp)
	}
}

func TestParseSentimentResponse(t *testing.T) {
	raw := []byte(`[[{"label":"POSITIVE","score":0.9}]]`)
	labels, err := parseSentimentResponse(raw)
	if err != nil || labels[0].Label != "POSITIVE" {
		t.Fatalf("err=%v labels=%v", err, labels)
	}
}
