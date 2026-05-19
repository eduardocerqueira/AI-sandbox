package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
)

// Use the namespaced id — hf-inference does not serve the shorthand repo name.
const defaultModel = "distilbert/distilbert-base-uncased-finetuned-sst-2-english"

// sentimentResponse is the typical shape for classification models on the Inference API.
type sentimentLabel struct {
	Label string  `json:"label"`
	Score float64 `json:"score"`
}

func inferSentiment(token, model, text string) ([]sentimentLabel, error) {
	url := fmt.Sprintf("https://router.huggingface.co/hf-inference/models/%s", model)
	body, err := json.Marshal(map[string]string{"inputs": text})
	if err != nil {
		return nil, err
	}

	req, err := http.NewRequest(http.MethodPost, url, bytes.NewReader(body))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Authorization", "Bearer "+token)
	req.Header.Set("Content-Type", "application/json")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	raw, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}
	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("inference API %s: %s", resp.Status, strings.TrimSpace(string(raw)))
	}

	return parseSentimentResponse(raw)
}

// parseSentimentResponse handles [[{label,score},...]] or [{label,score},...].
func parseSentimentResponse(raw []byte) ([]sentimentLabel, error) {
	var nested [][]sentimentLabel
	if err := json.Unmarshal(raw, &nested); err == nil && len(nested) > 0 {
		return nested[0], nil
	}

	var flat []sentimentLabel
	if err := json.Unmarshal(raw, &flat); err != nil {
		return nil, fmt.Errorf("unexpected response: %s", string(raw))
	}
	return flat, nil
}

func formatLabels(labels []sentimentLabel) string {
	var b strings.Builder
	for i, l := range labels {
		if i > 0 {
			b.WriteString(", ")
		}
		fmt.Fprintf(&b, "%s (%.3f)", l.Label, l.Score)
	}
	return b.String()
}
