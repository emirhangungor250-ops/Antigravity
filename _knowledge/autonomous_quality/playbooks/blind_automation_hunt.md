# Blind Automation Hunt — Kör Otomasyon Avı

**Çalışma sıklığı:** Perşembe UTC 00:00 (İstanbul 03:00)
**Hedef süre:** ≤ 45 dakika
**Çıktı:** Ürün dilinde rapor (weekly_brief'e akar) + 0-1 opsiyonel öneri PR

## Amaç

Bir işin gerçek doğası "anlama" gerektirdiği halde katı kurallarla (hardcoded liste, keyword dizisi, serbest metne regex) yapılmış yerleri bul. Bu hatanın adı **sessiz körlük**: patlamaz, hata vermez, demo'da düzgün görünür — sadece gerçek hayatın çeşitliliğinde sessizce eksik çalışır. Aylar sonra şans eseri fark edilir.

Tipik örnek: Marka_Bulma_Outreach projesi Instagram caption'larından marka tespit ederken caption'ı bir AI'ya okutmak yerine "@etiket var mı + bilinen marka listesinde mi" diye bakıyordu. Listede olmayan ve etiketlenmemiş her marka görünmez oluyordu — projenin asıl işi buydu.

Bu routine **düzeltme yapmaz**. Çünkü kör otomasyonu düzeltmek (kuralı → AI'ya çevirmek) her zaman davranışı değiştirir ve genelde para/zaman maliyeti getirir. Bu bir **ürün kararıdır**, kullanıcı verir. Routine'in işi: körlüğü bulmak ve kullanıcının anlayacağı dilde anlatmak.

## Ne aranıyor — kör otomasyonun imzası

Şu iki şart birlikte sağlanıyorsa bu kör otomasyondur:

1. **Girdi açık uçlu insan dili.** Caption, e-posta gövdesi, kullanıcı mesajı, serbest metin, isimler, kullanıcının yazdığı herhangi bir şey.
2. **Çıktı bir yargı.** "Bu iş birliği mi?", "Hangi marka geçiyor?", "Kullanıcı ne istiyor?", "Bu spam mı?", "Bu hangi kategori?" — sınıflandırma, çıkarım, niyet tespiti.

Ve bu yargı, AI yerine şunlardan biriyle yapılıyorsa:

- Hardcoded kelime/marka/isim listesinde `in` kontrolü
- `if "şu kelime" in metin` tarzı serbest metne string araması
- Serbest metni "anlamak" için regex (yapı çıkarmak değil — yargı üretmek)
- Keyword sayma + eşik ("2+ AI kelimesi varsa AI markasıdır")
- Niyet/kategori tespiti keyword eşleştirmeyle

## Ne kör otomasyon DEĞİL — bunları sakın işaretleme

- **Yapılı veriye regex.** E-posta formatı, telefon, URL, tarih, ID çıkarma — bunlar yapılı, regex doğru araç.
- **Kendi kontrollü string'lerine eşleştirme.** Config key'leri, enum değerleri, kendi ürettiğin sabit etiketler — açık uçlu insan dili değil.
- **Buton/seçim akışlarının deterministik state machine'i.** Buton akışları zaten deterministik OLMALI, LLM tool-calling'e bırakılmamalı. Bu doğru mimari, dokunma.
- **LLM'den önce hızlı ön-filtre.** Keyword bir optimizasyon olarak kullanılıp asıl kararı yine LLM veriyorsa — bu sağlıklı, körlük değil.

Ayrım net: deterministik kural **kontrollü girdi** için doğrudur (butonlar, kendi enum'ların). Kör otomasyon **açık uçlu girdide** yanlıştır (insandan gelen serbest metin).

## Adım adım

### 1) Repo'yu çek

```
git clone <GITHUB_REPO_URL> /tmp/antigravity
cd /tmp/antigravity
git checkout main
git pull --rebase origin main
```

### 2) Proje seç

`README.md` rotasyon formülü, offset = 28:

```python
import os, datetime
EXCLUDED = {"_arsiv", "Patron_Dashboard", "youtube-content-engine"}
projects = sorted([
    p for p in os.listdir("Projeler")
    if not p.startswith("_") and p not in EXCLUDED
    and os.path.isdir(f"Projeler/{p}")
])
epoch_day = (datetime.date.today() - datetime.date(2026, 5, 1)).days
project = projects[(epoch_day + 28) % len(projects)]   # offset=28 → blind_automation_hunt
print(f"Hedef: {project}")
```

`logs/blind_automation_hunt_<son-30-gün>.json` dosyalarına bak — aynı projeyi son ayda taradıysan sıradakine geç.

### 3) Projeyi tara

Önce projenin **asıl işini** anla: README'yi oku, ana pipeline'ı bul. "Bu proje hangi kararı veriyor, hangi insan girdisini işliyor?"

Sonra kod içinde şunları ara:

- Hardcoded `LIST = [...]` / `SET = {...}` — özellikle marka, isim, kelime, kategori listeleri. Nerede kullanılıyor? Açık uçlu metne karşı mı eşleştiriliyor?
- `if X in caption/text/body/message/bio` — sağ taraf insan girdisi mi?
- `re.findall` / `re.search` serbest metin üzerinde — yapı mı çıkarıyor (regex doğru), yoksa yargı mı üretiyor (kör)?
- `*_KEYWORDS`, `*_MARKERS`, `*_FILTERS` isimli sabitler — keyword tabanlı sınıflandırma işareti
- Fonksiyon adı `is_*`, `detect_*`, `classify_*`, `extract_*` ama içi keyword eşleştirme

Her aday için **gerçek hayat testi** uygula: "Bu girdi şöyle gelse (etiketlenmemiş marka, farklı kelime, yabancı dil, yazım hatası) sistem yakalar mıydı?" Cevap "hayır" ise kör otomasyon.

**Her projede en fazla 3 bulgu raporla.** Daha fazlası varsa en kritik 3'ünü seç (projenin asıl işine en yakın olanlar), gerisini `skipped`'a yaz.

### 4) Bulguyu ürün diline çevir — ZORUNLU

kullanıcı yazılımcı değil. Teknik dille raporlarsan anlamaz, rapor çöp olur. Her bulgu şu üç cümlelik kalıpta yazılır:

1. **Ne yapıyor:** "X projesi, [iş] yaparken [insan girdisini] gözle okumak yerine kelime listesine bakıyor."
2. **Neyi kaçırıyor:** "Listede olmayan / farklı yazılmış / etiketlenmemiş [şey] görünmez oluyor."
3. **Öneri:** "Bu adımı AI'ya okutsak, tıpkı senin gözünün yaptığı gibi kaçırmaz. Maliyet: [tahmin]."

İyi örnek: *"Marka takip projesi, Instagram açıklamalarındaki markaları gözle okumak yerine sabit bir marka listesine bakıyor. Listede olmayan markaları hiç görmüyor. Açıklamayı AI'ya okutsak kaçırmaz, ayda birkaç sent."*

Kötü örnek (ASLA böyle yazma): *"analyzer.py'da extract_mentions_from_caption regex'i sadece @handle yakalıyor, is_likely_ai_brand keyword threshold'u..."*

Maliyet tahmini ver: kaç çağrı x hangi model x tahmini aylık USD. kullanıcı maliyet-fayda kararını ancak rakamla verebilir.

### 5) Opsiyonel: öneri PR'ı

Düzeltme **açık ve net** ise (keyword adımını LLM çağrısına çevirmek doğrudan mümkün, mevcut yapıyı bozmuyor) bir öneri PR'ı açabilirsin. Açmazsan da sorun yok — asıl çıktı rapor.

- Branch: `autonomous/blind-automation-hunt/<tarih>-<proje>`
- Risk her zaman **medium veya high** — davranış değişiyor, asla main'e merge etme
- PR sadece bir öneridir, kullanıcı weekly_brief'ten görüp karar verir
- Eski keyword yolunu **silme** — yedek/fallback olarak bırak, LLM ana yol olsun
- LLM çağrısı eklerken `_skills/llm-structured-output-rules` ve `feedback_claude_opus_47_no_prefill` kurallarına uy: explicit schema + tool_use, prefill yok
- `python -m py_compile` ile doğrula

PR açtıysan body'de hem teknik özet hem de 4. adımdaki ürün dili özeti olsun (weekly_brief ürün dili kısmını kullanır).

### 6) Log yaz

`logs/blind_automation_hunt_<YYYY-MM-DD>.json`:

```json
{
  "routine": "blind_automation_hunt",
  "date": "<YYYY-MM-DD>",
  "project": "<proje>",
  "started_at": "<ISO>",
  "finished_at": "<ISO>",
  "findings": [
    {
      "severity": "high",
      "where": "src/analyzer.py — caption marka tespiti",
      "product_language": "Marka takip projesi açıklamalardaki markaları gözle okumak yerine sabit listeye bakıyor. Listede olmayanı hiç görmüyor. AI'ya okutsak kaçırmaz, ayda birkaç sent.",
      "real_world_test": "Etiketlenmemiş 'Synthix' markası → mevcut sistem kaçırır",
      "cost_estimate_usd_month": 0.05,
      "pr_url": null
    }
  ],
  "skipped": [],
  "errors": [],
  "duration_min": 31
}
```

`severity`: projenin asıl işini etkiliyorsa `high`, yan bir akışsa `medium`, kozmetikse `low`.

```bash
git checkout main
git pull --rebase origin main
git add _knowledge/autonomous_quality/logs/blind_automation_hunt_$(date +%F).json
git commit -m "chore(autonomous): blind_automation_hunt log — $(date +%F)"
git push origin main
```

### 7) Hata durumunda

- Proje çok büyük, 45 dk yetmedi → bulduklarını raporla, kalanı `skipped`'a yaz, çık
- PR push reddedildi → `git pull --rebase` + tekrar; iki kez başarısız → branch'i bırak, `errors`'a yaz, rapor yine de log'da kalsın
- Kör otomasyon bulamadıysan da log yaz: `findings: []`, `note: "Temiz tarama, kör otomasyon bulunmadı"`

### 8) Yapma

- **Asla** main'e otomatik düzeltme push etme — her kör otomasyon fix'i davranış değiştirir, PR olur
- **Asla** raporu teknik dille yaz — dosya adı, fonksiyon adı, regex'ten bahsetme; ürün dili zorunlu
- **Asla** yapılı veri regex'ini (e-posta, telefon, URL) kör otomasyon diye işaretleme
- **Asla** deterministik buton/seçim state machine'ini işaretleme — o doğru mimari
- **Asla** maliyet tahmini olmadan "AI kullan" önerme — kullanıcı rakamsız karar veremez
- **Asla** tek projede 3'ten fazla bulgu raporlama — en kritik 3, gerisi `skipped`

## Output kontrol

İş bitince log'da:
- `findings`: her biri ürün dilinde, gerçek hayat testli, maliyet tahminli
- `skipped`: 3 sınırı yüzünden veya zaman yüzünden bakılmayanlar
- `errors`: teknik başarısızlıklar
- `duration_min`: toplam süre

Bulgu varsa weekly_brief Pazartesi bunu "Kör Nokta" bölümünde ürün diliyle kullanıcıya iletir.
