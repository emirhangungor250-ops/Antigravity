// services/memory.js
// Supabase tabloları: ig_subscribers, ig_conversations
const { createClient } = require('@supabase/supabase-js');
const { config } = require('../config/env');
const log = require('../utils/logger');

const supabase = createClient(config.supabaseUrl, config.supabaseServiceRoleKey);

async function getHistory(subscriberId, limit = 20) {
  try {
    const { data, error } = await supabase
      .from('ig_conversations')
      .select('role, content, intent')
      .eq('subscriber_id', subscriberId)
      .order('created_at', { ascending: false })
      .limit(limit);
    if (error) throw error;
    return data.reverse();
  } catch (error) {
    log.error(`[memory] getHistory hatası: ${error.message}`, error);
    return [];
  }
}

async function saveMessage(subscriberId, role, content, meta = {}) {
  try {
    const { error } = await supabase
      .from('ig_conversations')
      .insert({
        subscriber_id: subscriberId,
        role,
        content,
        intent: meta.intent || null,
        model_used: meta.modelUsed || null
      });
    if (error) throw error;
  } catch (error) {
    log.error(`[memory] saveMessage hatası: ${error.message}`, error);
  }
}

async function getSubscriber(subscriberId) {
  try {
    const { data, error } = await supabase
      .from('ig_subscribers')
      .select('*')
      .eq('subscriber_id', subscriberId)
      .single();
    if (error && error.code !== 'PGRST116') throw error;
    return data;
  } catch (error) {
    log.error(`[memory] getSubscriber hatası: ${error.message}`, error);
    return null;
  }
}

async function createSubscriber(subscriberId, igUsername = null) {
  try {
    const { data, error } = await supabase
      .from('ig_subscribers')
      .insert({
        subscriber_id: subscriberId,
        ig_username: igUsername,
        language: 'tr',
        profile_json: {}
      })
      .select()
      .single();
    if (error) throw error;
    return data;
  } catch (error) {
    log.error(`[memory] createSubscriber hatası: ${error.message}`, error);
    return null;
  }
}

async function updateProfile(subscriberId, patch) {
  try {
    const current = await getSubscriber(subscriberId);
    const merged = { ...(current?.profile_json || {}), ...patch };
    const { error } = await supabase
      .from('ig_subscribers')
      .update({ profile_json: merged, last_seen_at: new Date().toISOString() })
      .eq('subscriber_id', subscriberId);
    if (error) throw error;
  } catch (error) {
    log.error(`[memory] updateProfile hatası: ${error.message}`, error);
  }
}

async function wasRecentlyProcessed(subscriberId, content, windowSeconds = 60) {
  try {
    const sinceIso = new Date(Date.now() - windowSeconds * 1000).toISOString();
    const { data, error } = await supabase
      .from('ig_conversations')
      .select('id')
      .eq('subscriber_id', subscriberId)
      .eq('role', 'user')
      .eq('content', content)
      .gte('created_at', sinceIso)
      .limit(1);
    if (error) throw error;
    return Array.isArray(data) && data.length > 0;
  } catch (error) {
    log.error(`[memory] wasRecentlyProcessed hatası: ${error.message}`, error);
    return false;
  }
}

module.exports = {
  getHistory,
  saveMessage,
  getSubscriber,
  createSubscriber,
  updateProfile,
  wasRecentlyProcessed,
  supabase
};
