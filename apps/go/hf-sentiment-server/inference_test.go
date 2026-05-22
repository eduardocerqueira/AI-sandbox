package main

import (
	"testing"
)

func TestParseSentimentResponse_nested(t *testing.T) {
	raw := []byte(`[[{"label":"POSITIVE","score":0.99}]]`)
	labels, err := parseSentimentResponse(raw)
	if err != nil {
		t.Fatal(err)
	}
	if labels[0].Label != "POSITIVE" {
		t.Fatalf("got %q", labels[0].Label)
	}
}

func TestParseSentimentResponse_flat(t *testing.T) {
	raw := []byte(`[{"label":"NEGATIVE","score":0.8}]`)
	labels, err := parseSentimentResponse(raw)
	if err != nil {
		t.Fatal(err)
	}
	if labels[0].Label != "NEGATIVE" {
		t.Fatalf("got %q", labels[0].Label)
	}
}

func TestNewSentimentClient_defaultModel(t *testing.T) {
	c := newSentimentClient("hf_test", "")
	if c.modelID() != defaultModel {
		t.Fatalf("got %q", c.modelID())
	}
}
