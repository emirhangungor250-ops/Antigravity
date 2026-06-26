// services/ai_expensive.js
// Claude Sonnet 4.6 wrapper — deep response generation.
// Tool support: escalate_to_dolunay, lookup_video.
const Anthropic = require('@anthropic-ai/sdk');
const { config } = require('../config/env');
const log = require('../utils/logger');

const client = new Anthropic({ apiKey: config.anthropicApiKey });

/**
 * Multi-turn generation with optional tool use.
 * @param {object} opts
 * @param {string} opts.system
 * @param {Array} opts.messages - [{ role, content: string|array }]
 * @param {Array} opts.tools - Anthropic tool definitions
 * @param {Function} opts.handleTool - async (toolName, toolInput, toolUseId) => string (tool_result content)
 * @param {number} opts.maxTokens
 * @param {number} opts.maxToolHops - safety cap
 * @returns {Promise<{ text: string, toolCalls: Array<{name,input}> }>}
 */
async function generate({
  system,
  messages,
  tools = [],
  handleTool = null,
  maxTokens = 1024,
  maxToolHops = 3
}) {
  const conversation = messages.map(m => ({ ...m }));
  const toolCalls = [];
  let hops = 0;
  let finalText = '';

  while (hops <= maxToolHops) {
    const response = await client.messages.create({
      model: config.modelExpensive,
      max_tokens: maxTokens,
      system,
      tools: tools.length > 0 ? tools : undefined,
      messages: conversation
    });

    const blocks = response.content || [];
    const toolUseBlocks = blocks.filter(b => b.type === 'tool_use');
    const textBlocks = blocks.filter(b => b.type === 'text');
    const text = textBlocks.map(b => b.text).join('\n').trim();

    if (toolUseBlocks.length === 0) {
      finalText = text;
      break;
    }

    conversation.push({ role: 'assistant', content: blocks });
    const toolResultsContent = [];
    for (const tu of toolUseBlocks) {
      toolCalls.push({ name: tu.name, input: tu.input });
      let resultStr = 'ok';
      if (typeof handleTool === 'function') {
        try {
          resultStr = await handleTool(tu.name, tu.input, tu.id);
        } catch (err) {
          log.error(`[ai_expensive] handleTool hatası: ${err.message}`, err);
          resultStr = `error: ${err.message}`;
        }
      }
      toolResultsContent.push({
        type: 'tool_result',
        tool_use_id: tu.id,
        content: String(resultStr)
      });
    }
    conversation.push({ role: 'user', content: toolResultsContent });
    hops++;

    if (response.stop_reason !== 'tool_use') {
      finalText = text;
      break;
    }
  }

  if (hops > maxToolHops) {
    log.warn(`[ai_expensive] maxToolHops aşıldı`);
  }

  return { text: finalText, toolCalls };
}

module.exports = { generate };
