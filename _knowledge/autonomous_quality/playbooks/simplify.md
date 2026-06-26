# Simplify — Otonom Refactor & Sadeleştirme

**Çalışma sıklığı:** Cumartesi UTC 01:00 (İstanbul 04:00)
**Hedef süre:** ≤ 60 dakika
**Çıktı:** Bir projenin duplikasyon/şişkinliği için commit (low-risk) veya PR (medium-risk)

## Amaç

Antigravity'deki projelerde zaman içinde biriken duplikasyon, dead code, gereksiz abstraction'ı temizle. `simplify` skill'inden ilham al ama daha disiplinli ol — refactor'lar tehlikelidir.

## Adım adım

### 1) Repo'yu çek

```
git clone <GITHUB_REPO_URL> /tmp/antigravity
cd /tmp/antigravity
git checkout main
git pull --rebase origin main
```

### 2) Proje seç

Rotasyon offset = 14.

```python
project = projects[(epoch_day + 14) % len(projects)]
```

### 3) Hedef türleri ara

Bu routine yalnızca şunları temizler — daha agresif refactor'a girme:

**A. Dead code (low-risk)**
- Import edildi ama hiç kullanılmadı (`ruff` veya `eslint --rule no-unused-vars` ile tarat)
- Tanımlandı ama hiç çağrılmadı (`vulture` veya manuel grep)
- `if False:` / `if 0:` blokları
- Yorum satırına alınmış 10+ satırlık eski kod (git'te zaten var)

**B. Trivial duplikasyon (low-risk)**
- Aynı dosyada birebir aynı 5+ satırlık blok 2+ kez → tek fonksiyona çıkar
- Aynı projedeki 2+ dosyada aynı util fonksiyon → projedeki `utils.py` veya `lib/` altına taşı
- **YASAK:** `_skills/shared/` altına util taşıma (memory: `feedback_shared_util_refactor_kisiti.md` — Railway rootDirectory yüzünden import edilemez)

**C. Trivial abstraction temizliği (low-risk)**
- Tek satırlık wrapper fonksiyon (sadece kütüphane çağrısını forward ediyor) → inline et
- 1 kez kullanılan helper class → kullanıldığı yere inline
- Sadece 1 alanı olan dataclass → tuple veya doğrudan değer
- Hiç override edilmeyen base class hiyerarşisi → flatten

**D. Sade kod düzeltmesi (low-risk)**
- `if x == True:` → `if x:`
- `len(x) == 0` → `not x`
- List comprehension yerine yazılmış for-append → comprehension'a
- F-string fırsatı kaçırılmış string concat
- Python `dict.get(k, None)` → `dict.get(k)`

**E. Fonksiyon/dosya bölme (medium-risk → PR)**
- 200+ satır tek fonksiyon → mantıksal birimlere böl
- 800+ satır tek dosya → modüllere böl
- Bu kategori HER ZAMAN PR olarak açılır, asla direkt commit değil

### 4) Hangi şeyleri yapMA

- **Asla** public API'yi (fonksiyon isimleri, signature'lar, modül yolları) değiştirme — kullanan başka proje var
- **Asla** ürün davranışını değiştir (LLM prompt'u, marka tonu, görsel akış)
- **Asla** dependency ekle (yeni kütüphane = yeni risk; mevcut araçla yap)
- **Asla** "daha hızlı" diye optimizasyon yap (premature optimization)
- **Asla** tek commit'te 10+ dosya değiştirme (atomic değişiklik)

### 5) Değişikliği uygula

```bash
# Her temizlik konusu için ayrı commit
git checkout main
# değişiklik uygula
python -m py_compile <değişen dosyalar>
pytest Projeler/<proje>/tests/ 2>&1 | tail -20    # mevcut testler hala geçiyor mu?
git add <dosyalar>
git commit -m "refactor(<proje>): otonom-kalite — <değişiklik özeti>

<detay: ne kaldırıldı / birleştirildi / sadeleştirildi>
Risk: low
Davranış değişmedi: <neden — testler geçiyor / public signature aynı>

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
git push origin main
```

Medium-risk (fonksiyon/dosya bölme) için PR aç (`autonomous/simplify/<tarih>-<proje>`).

### 6) Self-validation zorunluluğu

**Compile + test geçmeden hiçbir refactor commit etme.** Refactor sırasında en sık hata:
- Import yolu değişti, çağıran yerler güncellenmedi
- Variable rename'i tüm referansları kapsamadı
- Indentation/scope bozuldu

Bu yüzden:
1. Değişikliğin etki ettiği her dosyada `python -m py_compile` veya `node --check`
2. Projenin **tüm** test suite'i (`pytest Projeler/<proje>`, `npm test`)
3. Proje cron ise: `python <proje>/main.py --dry-run` veya equivalentini dene (memory'de `feedback_test_oncesi_self_validate.md`)
4. Test yoksa, en kritik fonksiyonun isim/signature aynı olduğunu grep'le doğrula

### 7) Log yaz

`logs/simplify_<YYYY-MM-DD>.json`:

```json
{
  "routine": "simplify",
  "project": "<proje>",
  "categories_addressed": ["dead_code", "trivial_dup"],
  "lines_removed": 87,
  "lines_added": 23,
  "files_changed": [...],
  "actions": [...],
  "skipped": [
    {"category": "function_split", "reason": "20dk içinde güvenli yapamadım, PR'a değil de bir sonraki haftaya"}
  ],
  "duration_min": 52
}
```

### 8) Hata durumunda

- Test başarısız → `git restore` ile sıfırla, başka bir kategoriye geç, errors'a yaz
- "Kullanılmadı" sanıp sildiğin import gerçekte dynamic import ile kullanılıyordu → revert + errors
- 60 dakika doldu, daha temizleyecek çok şey var → kalanları `skipped`'a yaz, çık

## Output kontrol

İdeal output: 30-100 satır kod silindi, 0-20 satır eklendi, testler hala geçiyor, davranış değişmedi.

Eğer "added > removed" çıktıysa, muhtemelen abstraction ekledin — bu routine'in işi değil. Revert et.
