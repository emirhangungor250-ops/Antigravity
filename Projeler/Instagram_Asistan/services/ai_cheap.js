// services/ai_cheap.js
// Claude Haiku 4.5 wrapper — cheap intent classifier + quick_response.
// Anthropic SDK; tool_use ile structured output (prefill kullanılmaz).
const Anthropic = require('@anthropic-ai/sdk');
const { config } = require('../config/env');
const log = require('../utils/logger');

const client = new Anthropic({ apiKey: config.anthropicApiKey });

/**
 * Single-shot structured output via tool_use.
 * @param {object} opts
 * @param {string} opts.system - system prompt
 * @param {Array} opts.messages - [{ role, content }] (user/assistant)
 * @param {object} opts.tool - { name, description, input_schema }
 * @param {number} opts.maxTokens
 * @returns {Promise<object>} tool input as plain object
 */
async function structuredCall({ system, messages, tool, maxTokens = 1024 }) {
  try {
    const response = await client.messages.create({
      model: config.modelCheap,
      max_tokens: maxTokens,
      system,
      tools: [tool],
      tool_choice: { type: 'tool', name: tool.name },
      messages
    });

    const toolBlock = (response.content || []).find(b => b.type === 'tool_use');
    if (!toolBlock || !toolBlock.input) {
      log.warn('[ai_cheap] tool_use bulunamadı, fallback parse', { stop_reason: response.stop_reason });
      const textBlock = (response.content || []).find(b => b.type === 'text');
      if (textBlock?.text) {
        try { return JSON.parse(textBlock.text); } catch (_) { /* fall through */ }
      }
      throw new Error('cheap: tool_use yok, parse edilemedi');
    }
    return toolBlock.input;
  } catch (err) {
    log.error(`[ai_cheap] structuredCall hatası: ${err.message}`, err);
    throw err;
  }
}

/**
 * Free-form short text call (rare; classifier ana yol değil).
 */
async function textCall({ system, messages, maxTokens = 512 }) {
  const response = await client.messages.create({
    model: config.modelCheap,
    max_tokens: maxTokens,
    system,
    messages
  });
  const textBlock = (response.content || []).find(b => b.type === 'text');
  return textBlock?.text?.trim() || '';
}

module.exports = { structuredCall, textCall };
