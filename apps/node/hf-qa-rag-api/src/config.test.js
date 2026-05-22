import assert from "node:assert/strict";
import test from "node:test";
import { getConfig } from "./config.js";

test("getConfig returns default values when env vars are not set", () => {
  const config = getConfig();
  assert.strictEqual(config.hfToken, "");
  assert.strictEqual(config.hfModel, "Qwen/Qwen2.5-1.5B-Instruct");
  assert.strictEqual(config.port, "8000");
  assert.match(config.knowledgePath, /knowledge\/qa\.txt$/);
});

test("getConfig returns trimmed values from env vars", () => {
  process.env.HF_TOKEN = "   my_token   ";
  process.env.HF_MODEL = "   my_model   ";
  process.env.PORT = "   3000   ";
  process.env.KNOWLEDGE_PATH = "   custom/path.txt   ";

  const config = getConfig();
  assert.strictEqual(config.hfToken, "my_token");
  assert.strictEqual(config.hfModel, "my_model");
  assert.strictEqual(config.port, "3000");
  assert.match(config.knowledgePath, /custom\/path\.txt$/);

  delete process.env.HF_TOKEN;
  delete process.env.HF_MODEL;
  delete process.env.PORT;
  delete process.env.KNOWLEDGE_PATH;
});
