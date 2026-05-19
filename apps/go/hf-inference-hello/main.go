package main

import (
	"flag"
	"fmt"
	"os"
	"strings"
)

var sampleTexts = []string{
	"I love learning Go!",
	"This compiler error is frustrating.",
	"Hugging Face Inference API is handy for small experiments.",
}

func main() {
	model := flag.String("model", defaultModel, "Hugging Face model id")
	text := flag.String("text", "", "Single text to classify (default: run built-in samples)")
	flag.Parse()

	token := strings.TrimSpace(os.Getenv("HF_TOKEN"))
	if token == "" {
		fmt.Fprintln(os.Stderr, "HF_TOKEN is not set. Export it or use: hf auth login")
		fmt.Fprintln(os.Stderr, "  export HF_TOKEN=hf_...")
		os.Exit(1)
	}

	texts := sampleTexts
	if *text != "" {
		texts = []string{*text}
	}

	fmt.Printf("Model: %s\n\n", *model)
	for _, t := range texts {
		labels, err := inferSentiment(token, *model, t)
		if err != nil {
			fmt.Fprintf(os.Stderr, "error for %q: %v\n", t, err)
			os.Exit(1)
		}
		fmt.Printf("%q -> %s\n", t, formatLabels(labels))
	}
}
