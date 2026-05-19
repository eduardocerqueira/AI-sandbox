package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
)

const defaultModel = "distilbert/distilbert-base-uncased-finetuned-sst-2-english"

type sentimentLabel struct {
	Label string  `json:"label"`
	Score float64 `json:"score"`
}

type classifier interface {
	modelID() string
	classify(text string) ([]sentimentLabel, error)
}

type sentimentClient struct {
	token string
	model string
	http  *http.Client
}

func newSentimentClient(token, model string) *sentimentClient {
	if model == "" {
		model = defaultModel
	}
	return &sentimentClient{
		token: token,
		model: model,
		http:  http.DefaultClient,
	}
}

func (c *sentimentClient) modelID() string {
	return c.model
}

func (c *sentimentClient) classify(text string) ([]sentimentLabel, error) {
	url := fmt.Sprintf("https://router.huggingface.co/hf-inference/models/%s", c.model)
	body, err := json.Marshal(map[string]string{"inputs": text})
	if err != nil {
		return nil, err
	}

	req, err := http.NewRequest(http.MethodPost, url, bytes.NewReader(body))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Authorization", "Bearer "+c.token)
	req.Header.Set("Content-Type", "application/json")

	resp, err := c.http.Do(req)
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
