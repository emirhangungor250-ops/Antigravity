// services/notion_videos.js
// Notion API client — kendi video içerik DB'nizi okur (.env NOTION_VIDEO_DB_ID).
// Beklenen properties (kendi şemana göre düzenle):
//   Name (title), Status (select), Caption (text), Drive (url),
//   Paylaşım Tarihi (date)
// Transcript page body'sindedir; gereksiz sayfa bölümlerini regex ile temizleyebilirsiniz.
const fetch = require('node-fetch');
const { config } = require('../config/env');
const log = require('../utils/logger');

const NOTION_API = 'https://api.notion.com/v1';
const NOTION_VERSION = '2022-06-28';

function headers() {
  return {
    'Authorization': `Bearer ${config.notionToken}`,
    'Notion-Version': NOTION_VERSION,
    'Content-Type': 'application/json'
  };
}

async function queryPublishedPages(opts = {}) {
  const allResults = [];
  let cursor = undefined;
  let pageNum = 0;
  do {
    const body = {
      filter: {
        property: 'Status',
        select: { equals: 'Yayınlandı' }
      },
      page_size: 100
    };
    if (cursor) body.start_cursor = cursor;

    const resp = await fetch(`${NOTION_API}/databases/${config.notionVideoDbId}/query`, {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify(body)
    });
    if (!resp.ok) {
      const txt = await resp.text();
      throw new Error(`Notion query failed (${resp.status}): ${txt}`);
    }
    const json = await resp.json();
    allResults.push(...(json.results || []));
    cursor = json.has_more ? json.next_cursor : undefined;
    pageNum++;
    if (pageNum > 50) {
      log.warn('[notion_videos] pagination cap reached (50 pages)');
      break;
    }
  } while (cursor);
  log.info(`[notion_videos] ${allResults.length} published page bulundu`);
  return allResults;
}

function extractPropertyText(prop) {
  if (!prop) return '';
  if (prop.type === 'title') return (prop.title || []).map(t => t.plain_text).join('');
  if (prop.type === 'rich_text') return (prop.rich_text || []).map(t => t.plain_text).join('');
  if (prop.type === 'url') return prop.url || '';
  if (prop.type === 'select') return prop.select?.name || '';
  if (prop.type === 'date') return prop.date?.start || '';
  return '';
}

function pageMetadata(page) {
  const props = page.properties || {};
  return {
    notion_page_id: page.id,
    last_edited_time: page.last_edited_time,
    video_title: extractPropertyText(props['Name']),
    caption: extractPropertyText(props['Caption']),
    drive_url: extractPropertyText(props['Drive']),
    publish_date: extractPropertyText(props['Paylaşım Tarihi']) || null,
    notion_url: page.url
  };
}

async function fetchPageBlocks(pageId) {
  const allBlocks = [];
  let cursor = undefined;
  let pageNum = 0;
  do {
    const url = new URL(`${NOTION_API}/blocks/${pageId}/children`);
    url.searchParams.set('page_size', '100');
    if (cursor) url.searchParams.set('start_cursor', cursor);

    const resp = await fetch(url.toString(), { headers: headers() });
    if (!resp.ok) {
      const txt = await resp.text();
      throw new Error(`Notion blocks failed (${resp.status}): ${txt}`);
    }
    const json = await resp.json();
    allBlocks.push(...(json.results || []));
    cursor = json.has_more ? json.next_cursor : undefined;
    pageNum++;
    if (pageNum > 20) break;
  } while (cursor);
  return allBlocks;
}

function blockToText(block) {
  const t = block.type;
  if (!t) return '';
  const data = block[t];
  if (!data) return '';

  const rich = data.rich_text;
  if (Array.isArray(rich)) {
    return rich.map(r => r.plain_text).join('');
  }
  return '';
}

// Page body'den script metnini çıkar. Şu separator'lardan SONRASI atılır:
// 1. "## 🎬 YOUTUBE KAPAK REVİZYON PANELİ" — internal not
// 2. Tek başına "---" divider — kapak panel'i ya da meta bilgi
function extractScriptText(blocks) {
  const STOP_HEADING_RE = /YOUTUBE\s+KAPAK\s+REV[İI]ZYON\s+PANEL[İI]/i;
  const lines = [];
  for (const block of blocks) {
    const t = block.type;
    if (t === 'divider') {
      // İlk divider script'in sonu olabilir. Heuristik: lines uzunluğu > 200 char ise stop.
      if (lines.join(' ').length > 200) break;
      continue;
    }
    if (t === 'heading_1' || t === 'heading_2' || t === 'heading_3') {
      const txt = blockToText(block).trim();
      if (STOP_HEADING_RE.test(txt)) break;
      if (txt) lines.push(txt);
      continue;
    }
    if (t === 'image' || t === 'embed' || t === 'video' || t === 'file') continue;
    if (t === 'child_page' || t === 'link_to_page') continue;
    const txt = blockToText(block).trim();
    if (txt) lines.push(txt);
  }
  return lines.join('\n').trim();
}

function chunkText(text, maxChars = 2200, overlap = 200) {
  if (!text) return [];
  const chunks = [];
  let i = 0;
  while (i < text.length) {
    let end = Math.min(i + maxChars, text.length);
    if (end < text.length) {
      const lastBreak = text.lastIndexOf('\n', end);
      if (lastBreak > i + 500) end = lastBreak;
    }
    chunks.push(text.slice(i, end).trim());
    if (end >= text.length) break;
    i = Math.max(end - overlap, i + 1);
  }
  return chunks.filter(c => c.length > 30);
}

module.exports = {
  queryPublishedPages,
  pageMetadata,
  fetchPageBlocks,
  extractScriptText,
  chunkText
};
