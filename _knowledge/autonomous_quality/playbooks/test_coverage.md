# Test Coverage — Otonom Test Yazımı

**Çalışma sıklığı:** Salı + Cuma UTC 00:00 (İstanbul 03:00)
**Hedef süre:** ≤ 45 dakika
**Çıktı:** Bir projeye yeni test dosyası/dosyaları, hepsi `main` branch'e direkt commit (test yazımı low-risk).

## Amaç

Antigravity projelerinin çoğunda ya hiç test yok ya da sığ. Bu routine her hafta 2 kez bir projeye **kritik path testleri** ekler. Var olan kod davranışını dondurma amacı — regresyonu yakalamak için.

## Adım adım

### 1) Repo'yu çek

```
git clone <GITHUB_REPO_URL> /tmp/antigravity
cd /tmp/antigravity
git checkout main
git pull --rebase origin main
```

### 2) Proje seç

Rotasyon offset = 7. Aynı README formülü:

```python
project = projects[(epoch_day + 7) % len(projects)]
```

`logs/test_coverage_<son-30-gün>.json` dosyalarına bak — son 30 gün içinde aynı proje tarandıysa, bir sonrakine geç.

### 3) Mevcut test durumunu öl

Projede ne var?

```bash
find Projeler/<proje> -name "test_*.py" -o -name "*_test.py" -o -name "*.test.js" -o -name "*.spec.js"
```

Test dosyası YOKSA → "first tests" modu (en kritik 3 path için baştan test yaz).
Test dosyası VARSA → "gap fill" modu (kapsama dışındaki kritik fonksiyonları bul).

### 4) Test framework'ü tespit et

- `requirements.txt` veya `pyproject.toml`'da `pytest` var mı? → pytest kullan
- `package.json`'da `jest`, `vitest`, `mocha`? → mevcut olanı kullan
- Hiçbiri yok? → Python projeleri için pytest ekle (`requirements-dev.txt`'e `pytest==8.3.4`)

### 5) Kritik path'leri seç

Şu fonksiyon türleri önceliklidir:

- **Dış servise istek atan fonksiyonlar** (API call, DB write, mail gönderim) — happy path + 1 hata path
- **State değiştiren fonksiyonlar** (DB row insert/update, dosya yazımı) — idempotency + error rollback
- **Karar fonksiyonları** (LLM çıktısı parse, kategorize, dispatch) — beklenen + sınır + bozuk input
- **Format/parse fonksiyonları** (telefon, e-posta, JSON parse) — geçerli + geçersiz + edge case

**Test edilmez:**
- `main()` veya entry point'ler (genelde I/O'ya bağımlı)
- Saf wrapper'lar (sadece kütüphane çağrısını forward eder)
- Trivially correct fonksiyonlar (constant return)

### 6) Test yaz

Test dosyası `Projeler/<proje>/tests/test_<modül>.py` veya proje konvansiyonuna uyan yere.

**Kurallar:**
- Her test ≤ 20 satır, tek davranışı doğrular
- Dış servis çağrılarını mock'la (`unittest.mock`, `pytest-mock`)
- Veritabanı kullanan projeler için: in-memory SQLite veya `pytest.fixture` ile geçici db
- Test isimleri `test_<davranış>_<koşul>` formatında (örn `test_send_mail_retries_on_429`)
- AAA pattern: Arrange / Act / Assert ayrımı her test'te belli

**Mock politikası:** memory'deki `feedback_simulasyon_mail_bypass.md` ve `feedback_multi_turn_test_zorunlu.md` kurallarına uy:
- Telegram/WhatsApp botlarda multi-turn senaryolar (5+ turn) ekle
- Mail/dış API mock'larda `SIMULATION_MODE` env veya prefix guard koruması
- Test dış API'ye gerçek istek atmamalı

### 7) Testleri çalıştır

```bash
cd Projeler/<proje>
pytest tests/ -v 2>&1 | tail -40
# veya
npm test 2>&1 | tail -40
```

Test geçmiyorsa:
- Önce **test'in kendisinin** bozuk olup olmadığına bak (mock yanlış, assert yanlış)
- Kod gerçekten bozuksa **bu routine değil bug_hunt'ın işi** — testi geçici olarak skip'le (`@pytest.mark.skip(reason="bug_hunt routine fix etmeli: <link>")`) ve `errors` field'ına yaz
- Asla mevcut kodu değiştirip testi geçirme (bu routine kod yazmaz, test yazar)

### 8) Commit + push

```bash
git add Projeler/<proje>/tests/
git commit -m "test(<proje>): otonom-kalite — <N> yeni test eklendi

Kapsama: <hangi fonksiyonlar>
Framework: pytest / jest / ...
Risk: low (sadece test eklendi, kod değişmedi)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
git push origin main
```

Eğer `requirements-dev.txt` veya `package.json` değiştiyse, o değişikliği AYRI commit yap:

```bash
git commit -m "chore(<proje>): pytest dev dependency eklendi"
```

### 9) Log yaz

`logs/test_coverage_<YYYY-MM-DD>.json` dosyasını yaz, commit'le, push'la.

```json
{
  "routine": "test_coverage",
  "project": "<proje>",
  "mode": "first_tests | gap_fill",
  "tests_added": 7,
  "framework": "pytest",
  "coverage_before_pct": null,
  "coverage_after_pct": null,
  "actions": [...],
  "skipped_tests": [
    {"name": "test_x", "reason": "Mevcut kod bug'lu, bug_hunt fix etmeli"}
  ],
  "duration_min": 38
}
```

`coverage_*` field'ları opsiyonel — `pytest-cov` veya `c8` mevcutsa çalıştır, yoksa boş bırak.

### 10) Yapma

- **Asla** kod davranışını değiştirme (test yaz, kod değiştirme)
- **Asla** dış servise gerçek istek atan test ekleme
- **Asla** flaky test (`time.sleep`, network'e dependent) yazma
- **Asla** mevcut test'i sil/değiştir (gap-fill modunda bile)
- **Asla** test dosyasında secrets/token kullanma — `pytest.fixture` ile fake değer üret
- **Asla** main()/entry point için integration test ekleme (bu işin scope'u dışında)

## Output kontrol

Test sayısı 0 olsa bile log yazılmalı — sebep `note` field'ına: "Proje için kritik path yoktu, smoke test mevcut, gap_fill modunda ekleme gereği görülmedi".
