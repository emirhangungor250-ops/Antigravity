// scripts/seed_kb_factory.js
// RAG-A — <TOPLULUK_ADI> KB markdown'ını knowledge_chunks tablosuna source='main' ile yükler.
// Önce eski source='main' kayıtlarını siler, sonra yeniden seed yapar.
const fs = require('fs');
const path = require('path');
const OpenAI = require('openai');
const { config } = require('../config/env');
const { supabase } = require('../services/memory');
const log = require('../utils/logger');

const openai = new OpenAI({ apiKey: config.openaiApiKey });

const KB_CANDIDATES = [
  path.join(__dirname, '..', 'data', 'main-asistan-bilgi-tabani-v7.md'),
  path.join(__dirname, '..', '..', 'Whatsapp_Asistan', 'main-asistan-bilgi-tabani-v7.md')
];

async function main() {
  let mdContent = null;
  let sourcePath = null;
  for (const p of KB_CANDIDATES) {
    if (fs.existsSync(p)) {
      mdContent = fs.readFileSync(p, 'utf8');
      sourcePath = p;
      break;
    }
  }
  if (!mdContent) {
    throw new Error(`KB markdown bulunamadı. Arandı:\n${KB_CANDIDATES.join('\n')}`);
  }
  log.info(`[seed] KB okundu: ${sourcePath}`);

  const chunks = [];
  const lines = mdContent.split('\n');
  let currentSection = '', currentTitle = '', currentContent = [];
  for (const line of lines) {
    if (line.startsWith('## ') || line.startsWith('### ')) {
      if (currentContent.length > 0 && currentTitle) {
        chunks.push({ section: currentSection || '0', section_title: currentTitle, content: currentContent.join('\n').trim() });
        currentContent = [];
      }
      const titleText = line.replace(/^#+\s/, '');
      const sectionMatch = titleText.match(/^([\d.]+)\s*/);
      if (sectionMatch) {
        currentSection = sectionMatch[1].trim();
        currentTitle = titleText.substring(sectionMatch[0].length).trim();
      } else {
        currentTitle = titleText;
      }
    } else {
      currentContent.push(line);
    }
  }
  if (currentContent.length > 0 && currentTitle) {
    chunks.push({ section: currentSection || '0', section_title: currentTitle, content: currentContent.join('\n').trim() });
  }

  log.info(`[seed] ${chunks.length} chunk parsed`);

  const { error: delError } = await supabase
    .from('knowledge_chunks')
    .delete()
    .eq('source', 'main');
  if (delError) log.warn(`[seed] delete eski kayıtlar: ${delError.message}`);

  let processed = 0, failed = 0;
  for (const chunk of chunks) {
    if (!chunk.content || chunk.content.trim() === '') continue;
    try {
      const e = await openai.embeddings.create({
        model: 'text-embedding-3-small',
        input: `[${chunk.section_title}]\n${chunk.content}`,
        dimensions: 1536
      });
      const { error } = await supabase.from('knowledge_chunks').insert({
        section: chunk.section,
        section_title: chunk.section_title,
        content: chunk.content,
        embedding: e.data[0].embedding,
        metadata: { seeded_at: new Date().toISOString(), source_file: path.basename(sourcePath) },
        source: 'main'
      });
      if (error) {
        failed++;
        log.warn(`[seed] ${chunk.section_title} insert hatası: ${error.message}`);
      } else {
        processed++;
      }
    } catch (err) {
      failed++;
      log.warn(`[seed] ${chunk.section_title} embedding hatası: ${err.message}`);
    }
    await new Promise(r => setTimeout(r, 120));
  }

  log.info(`[seed] DONE total=${chunks.length} processed=${processed} failed=${failed}`);
}

if (require.main === module) {
  main().then(() => process.exit(0)).catch(err => {
    log.error(`[seed] fatal: ${err.message}`, err);
    process.exit(1);
  });
}

module.exports = { main };
