package main

import (
	"strings"
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

func TestFormatLabels(t *testing.T) {
	out := formatLabels([]sentimentLabel{{"POSITIVE", 0.991}})
	if !strings.Contains(out, "POSITIVE") || !strings.Contains(out, "0.991") {
		t.Fatalf("unexpected: %s", out)
	}
}
