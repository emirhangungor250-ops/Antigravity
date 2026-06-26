# ManyChat Akışı — Öğrenilen Kurallar (TARZ ŞABLONU)

Bu dosya her üretimde prompt'a enjekte edilir; üretilecek akışın TARZINI bu dosya belirler.
Aşağıdakiler iyi çalışan örnek bir kural setidir. **Kendi markanın diline göre düzenle.**
Bir akışı beğenmediğinde buraya yeni bir kural ekle, ilgili paneli sildirip yeniden ürettir.

## 🟦 Akış deseni

- DM tek mesaj değil, SOHBET akışıdır: açılış balonu + gerekirse butona basınca açılan takip mesajları.
- Açılış = kısa merak/değer teaser (1-3 cümle). Her şeyi açılışta dökme; değeri takip mesajına yay.
- Basit videoda tek balon yeter (açılışta kısa anlatım + 1 link butonu). Gereksiz balon ekleme.
- Adım adım tutorial videoda: açılış balonu komple numaralı rehber olabilir (1️⃣2️⃣3️⃣…) + 1 link.

## 🔘 Butonlar

- Sayı İHTİYACA göre, çoğu zaman 1, en fazla 3. ASLA doldurmak için 3'e tamamlama.
- İki tip: LINK (araç/site/store, kaynak havuzundan asset_ref ile) ve DEVAM ("Öğren", "Nasıl yani?",
  "Özellikleri Öğren", "Örnekleri Gör", "Biraz daha ara" — sohbeti ilerletir).
- Etiket kısa ve net: marka adı ("Printify", "MiniMax") veya konuşma dili devam etiketi.
- Jenerik etiket ("Detay", "Resmi sayfa") YASAK.
- Link URL'i metne YAZILMAZ; sadece link butonu olur (havuzdan gerçek URL).

## 💬 Takip mesajının içeriği (videonun vaadine göre)

- Adım adım rehber (numaralı) — nasıl-yapılır videosu.
- Kupon/indirim — ayrı, son mesajda, konuşma dilinde (örn. "üye olurken bu kodu kullan: KODUN").
- Özellik listesi — ✳️ veya numaralı maddeler.
- Fiyat, store linkleri, kısa açıklama.

## 🗣️ Ton

- Sıcak, "sen" dili, ÇOK basit, kısa cümle (max 15 kelime). "Selam, konu çok basit." havası.
- Emoji ölçülü (👇🫣✨😎👋). Em-dash (—) YASAK. HTML etiketi YASAK.
- Markanın istediği emoji ailesini buraya yaz; istemediklerini de (örn. kalp ailesi 🫶 ❤️ 🥰 😍).

## 🔸 Madde işareti

- Madde işareti: sıralı adım → 1️⃣2️⃣3️⃣…, paralel madde → 🔹 veya ✳️ (görünür emoji).
- ◇ ◆ ▸ • ● gibi GEOMETRİK karakterler Notion'da GÖRÜNMÜYOR. ASLA kullanma.

## ✂️ Az kelime + ton

- Açılış (KART 1) ÇOK kısa olsun (1-2 cümle); orada hızlıca ilgi çekiyoruz. Gereksiz kelime yok.
- Tüm kartlarda kelime sayısını azalt; her cümle bir iş yapsın, dolgu cümle yok.

## 📑 Brief + yorum

- Sayfa yorumları + marka brief'i ekstra kaynaktır: kupon, affiliate link, doğru indirim/fiyat orada olabilir.
- Brief markanın BAĞLAYICI resmi kaynağıdır. İndirim/fiyat/link script ile çelişirse BRIEF kazanır
  (örn. script %15 ama brief %12 → %12 yaz). Hikaye/kanca script'ten gelir.
- Yorumlardan sadece GERÇEK değer bilgisini al; ekip notu, kişi ismi, üretim sohbeti DM'e sızdırma.

## ⚠️ Kontrol notları

- Belirsizlikte kullanıcıya not bırak; ama not ÇOK KISA + ÇOK BASİT olsun: tek cümle, ~10 kelime, jargonsuz.
- Örnek: "İndirim %12 olmalı, videoda %15 geçiyor. Kontrol et." Uzun/teknik açıklama yazma.

## ✅ Dürüstlük

- Kupon kodu / indirim oranı / fiyat / sayı: SADECE scriptte varsa ve AYNEN. Yoksa UYDURMA.
- Script indirim oranı veriyor ama kodu vermiyorsa: oranı söyle, olmayan kod string'i uydurma.
- "Özel PDF/doküman hazırladım" gibi olmayan vaat YASAK. Gerçek değeri ver.

## 🚫 Doğrudan tanıtım

- Topluluk/kurs/eğitim adını doğrudan pazarlama YASAK (kendi markandaki yasak ifadeleri buraya yaz).
- Değer ver, tanıtım kendiliğinden gelir. "Ücretsiz üyelik hediyem var" gibi değer-çerçevesi serbest.
- Link kaynağı yoksa (kendi hizmetin) link butonu kullanma; değer/rehber + devam butonu kur.
- Yasak ifade listesini koda da yansıtmak istersen `core/sanitize.py` içindeki `BRAND_PROMO_PHRASES`'i düzenle.

## 🎯 Tetik

- Scriptin kapanışında söz verilen tetik (GÖNDER, DENE, TATİL, GÖRSEL…) varsa onu kullan.
- Yoksa konuya özel tek kelime, BÜYÜK harf, sade Türkçe türet.
