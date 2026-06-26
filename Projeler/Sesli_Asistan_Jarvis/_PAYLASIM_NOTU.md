# Paylaşım Notu — Sesli Asistan (JARVIS)

**Mod:** C (şablona çevrildi)

## Ne yapıldı

- **Çıkarılan sahibe özel "canlı yayın reklam şovu" akışı (öğrenciye yaramaz):**
  Paket sahibinin Higgsfield/fal tabanlı, canlı yayında ürün reklamı üreten kişisel
  gösterisi tamamen kaldırıldı. Çıkarılan modüller: ürünün tarayıcıda görünür üretimi,
  ikinci monitör showu, gösteri girişi, masaüstü/ekran ürün hazırlığı ve fal ile reklam
  görseli üretici + tam-ekran slayt gösterici. Bu akışa bağlı `[ACTION:MAKE_ADS]`,
  `[ACTION:SHOW_ADS]`, `[ACTION:SHOW_PRODUCT]` komutları ve sunucudaki çağrıları temizlendi;
  uygulama artık bunlar olmadan sorunsuz import edilip derleniyor.
  - Higgsfield'e özel Chrome başlatma scripti de çıkarıldı (genel kullanıma açık değildi).

- **Jenerikleştirilen kişisel kimlik:**
  - Sabit kodlanmış kullanıcı adı ("...Bey") → `USER_NAME` env'i. Doldurulmazsa asistan
    isimsiz, kibar Türkçe hitapla ("efendim") konuşur. Sistem promptu artık `{USER_NAME}`
    şablonu kullanır.
  - Tüm sesli yanıt metinlerindeki kişisel ad isimsiz hitaba indirildi; sahibin ses
    kimliği (özel ses id'si) jenerik bir varsayılana çevrildi, env'den okunur.
  - Sahibin makinesine özel bir mutlak yol veya gizli `master.env` referansı KALMADI
    (bunların hepsi çıkarılan reklam modüllerindeydi).

- **Model varsayılanı ucuza çekildi:** LLM çağrıları OpenRouter üzerinden gider;
  varsayılan model `openai/gpt-4o-mini` (ucuz). Pahalı model varsayılanı KONMADI;
  isteyen env ile güçlü modele çevirir.

- **`.env.example` baştan jenerik yazıldı:** açık `<...>` placeholder'larla — OpenRouter
  (beyin), ElevenLabs/Fish (ses) + ses kimliği, opsiyonel model seçimi, `USER_NAME`,
  takvim hesapları, hava durumu.

- **Orijinal yazar atfı korundu:** `LICENSE` dosyası orijinal sahibine ait olduğu gibi
  bırakıldı. README ve CLAUDE.md'ye "orijinal: Ethan Rogers, jenerikleştirildi" notu
  eklendi. README baştan jenerik (ne olduğu + backend/frontend kurulumu + env) yazıldı.

- **Kopyaya alınmayanlar (allowlist dışı):** sahibin iç devir/çalışma notu (`HANDOVER`),
  derlenmiş ikili dosyalar (Swift binary'leri — kaynak `.swift`'ler kaldı, öğrenci derler),
  kaynak zip arşivi, ayrı bir kurulum-prompt belgesi, gerçek `.env`, çalışma anı veritabanı
  ve önbellekler.

- **Doğrulama:** Tüm Python modülleri (`server.py` dahil) reklam akışı çıkarıldıktan sonra
  hatasız derlendi (py_compile). Eşzamanlı (sync) testler geçti; asenkron testler yalnızca
  yerelde eksik bir test eklentisi yüzünden atlandı (kodla ilgisi yok). Kişisel veri/yol
  taraması temiz çıktı.

## Öğrenci ne yapmalı

1. `.env.example` → `.env` kopyala ve doldur:
   - **Beyin:** `OPENROUTER_API_KEY` (openrouter.ai).
   - **Ses:** `ELEVENLABS_API_KEY` + `ELEVENLABS_VOICE_ID` (elevenlabs.io).
     ElevenLabs yerine `FISH_API_KEY` + `FISH_VOICE_ID` (fish.audio) de kullanılabilir.
   - **İsteğe bağlı:** `USER_NAME` (asistanın sana nasıl hitap edeceği — boşsa "efendim"),
     `JARVIS_MODEL` (daha güçlü model istersen), `CALENDAR_ACCOUNTS`.
2. Bağımlılıkları kur: `pip install -r requirements.txt`, sonra `cd frontend && npm install`.
3. Çalıştır: backend `python server.py`, frontend `cd frontend && npm run dev`
   (ya da tek komut: `./baslat.sh`). Tarayıcıda sayfayı bir kez tıkla, sesi aç, konuş.
4. macOS gerekir: Takvim/Mail/Notlar erişimi AppleScript iledir; ilk kullanımda macOS
   izin isteyebilir (Mail sadece okuma, güvenlik için bilerek).

## Orijinal amaç → yeni jenerik çerçeve

- **Orijinal:** Açık kaynak JARVIS sesli asistanı (Ethan Rogers), paket sahibi tarafından
  bir canlı yayın için uyarlanmış: kullanıcı adı koda gömülü, LLM OpenRouter'a taşınmış ve
  sahibe özel bir Higgsfield/fal "reklam üretim şovu" eklenmişti.
- **Yeni:** Herkesin kendi anahtarlarıyla Mac'inde çalıştırabileceği jenerik, Türkçe
  konuşan sesli asistan. Çekirdek tam korundu: sesli sohbet, Takvim/Mail/Notlar erişimi,
  hafıza, gün planlama, web arama/gezinme, ekran farkındalığı, görev/not yönetimi ve
  Claude Code ile geliştirme. Yalnızca sahibe özel canlı-yayın reklam akışı çıkarıldı;
  hitap, ses kimliği ve model seçimi env ile parametreli.
