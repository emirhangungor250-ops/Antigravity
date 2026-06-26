// config/env.js
require('dotenv').config();

const requiredEnvs = [
  'MANYCHAT_API_TOKEN',
  'MANYCHAT_FIELD_ID_IG',
  'MANYCHAT_FLOW_ID_IG',
  'ANTHROPIC_API_KEY',
  'OPENAI_API_KEY',
  'SUPABASE_URL',
  'SUPABASE_SERVICE_ROLE_KEY',
  'NOTION_TOKEN',
  'GROQ_API_KEY'
];

for (const env of requiredEnvs) {
  if (!process.env[env]) {
    throw new Error(`EnvironmentError: Gerekli ortam değişkeni eksik: ${env}`);
  }
}

const config = {
  manychatApiToken: process.env.MANYCHAT_API_TOKEN,
  manychatFieldId: process.env.MANYCHAT_FIELD_ID_IG,
  manychatFlowId: process.env.MANYCHAT_FLOW_ID_IG,
  manychatProductCardsFlowId: process.env.MANYCHAT_FLOW_ID_PRODUCT_CARDS || null,
  manychatBasariIzlenmeFlowId: process.env.MANYCHAT_FLOW_ID_BASARI_IZLENME || null,
  manychatBasariGelirFlowId: process.env.MANYCHAT_FLOW_ID_BASARI_GELIR || null,
  manychatBasariIsletmeFlowId: process.env.MANYCHAT_FLOW_ID_BASARI_ISLETME || null,
  groqApiKey: process.env.GROQ_API_KEY,
  anthropicApiKey: process.env.ANTHROPIC_API_KEY,
  modelCheap: process.env.MODEL_CHEAP || 'claude-haiku-4-5',
  modelExpensive: process.env.MODEL_EXPENSIVE || 'claude-sonnet-4-6',
  openaiApiKey: process.env.OPENAI_API_KEY,
  supabaseUrl: process.env.SUPABASE_URL,
  supabaseServiceRoleKey: process.env.SUPABASE_SERVICE_ROLE_KEY,
  notionToken: process.env.NOTION_TOKEN,
  notionVideoDbId: process.env.NOTION_VIDEO_DB_ID || '<NOTION_DB_ID>',
  resendApiKey: process.env.RESEND_API_KEY || null,
  escalationEmail: process.env.ESCALATION_EMAIL || '<EMAIL>',
  webhookSecret: process.env.INSTAGRAM_WEBHOOK_SECRET || null,
  adminSecret: process.env.ADMIN_SECRET || null,
  rateLimitMax: parseInt(process.env.RATE_LIMIT_MAX || '10', 10),
  rateLimitWindowH: parseInt(process.env.RATE_LIMIT_WINDOW_H || '24', 10),
  coalesceInitialMs: parseInt(process.env.COALESCE_INITIAL_MS || '3000', 10),
  coalesceStragglerMs: parseInt(process.env.COALESCE_STRAGGLER_MS || '1500', 10),
  coalesceMaxIter: parseInt(process.env.COALESCE_MAX_ITER || '4', 10),
  port: process.env.PORT || 3457,
  simulationMode: process.env.SIMULATION_MODE === 'true'
};

module.exports = { config };
