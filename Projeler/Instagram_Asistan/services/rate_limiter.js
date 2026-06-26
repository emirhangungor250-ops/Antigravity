// services/rate_limiter.js
// F1 — Per subscriber rolling 24h window rate limit.
// Burst coalesce penceresindeki birden fazla mesaj 1 token sayılır (lock öncesi check).
const { supabase } = require('./memory');
const { config } = require('../config/env');
const log = require('../utils/logger');

const RATE_LIMIT_MSG = "Bu kanaldan günlük cevaplama kotanız doldu. Yarın tekrar yazabilir, ya da topluluğumuzdan birebir destek alabilirsin: <TOPLULUK_URL>";

async function checkAndConsume(subscriberId, opts = {}) {
  const max = opts.max ?? config.rateLimitMax;
  const windowH = opts.windowHours ?? config.rateLimitWindowH;
  try {
    const { data, error } = await supabase.rpc('ig_check_rate_limit', {
      p_subscriber_id: subscriberId,
      p_max: max,
      p_window_hours: windowH
    });
    if (error) throw error;
    const row = Array.isArray(data) ? data[0] : data;
    const allowed = !!row?.allowed;
    const currentCount = row?.current_count ?? 0;
    if (!allowed) {
      return { allowed: false, count: currentCount, max };
    }
    const { error: insertError } = await supabase
      .from('ig_rate_limits')
      .insert({ subscriber_id: subscriberId });
    if (insertError) {
      log.warn(`[rate_limiter] insert hatası: ${insertError.message}`);
    }
    return { allowed: true, count: currentCount + 1, max };
  } catch (err) {
    log.error(`[rate_limiter] checkAndConsume hatası: ${err.message}`, err);
    return { allowed: true, count: 0, max, failOpen: true };
  }
}

async function currentCount(subscriberId, opts = {}) {
  const windowH = opts.windowHours ?? config.rateLimitWindowH;
  try {
    const { data, error } = await supabase.rpc('ig_check_rate_limit', {
      p_subscriber_id: subscriberId,
      p_max: 999999,
      p_window_hours: windowH
    });
    if (error) throw error;
    const row = Array.isArray(data) ? data[0] : data;
    return row?.current_count ?? 0;
  } catch (err) {
    log.error(`[rate_limiter] currentCount hatası: ${err.message}`, err);
    return -1;
  }
}

async function resetSubscriber(subscriberId) {
  try {
    const { error } = await supabase
      .from('ig_rate_limits')
      .delete()
      .eq('subscriber_id', subscriberId);
    if (error) throw error;
    log.info(`[rate_limiter] reset`, { subscriberId });
  } catch (err) {
    log.error(`[rate_limiter] resetSubscriber hatası: ${err.message}`, err);
  }
}

module.exports = { checkAndConsume, currentCount, resetSubscriber, RATE_LIMIT_MSG };
