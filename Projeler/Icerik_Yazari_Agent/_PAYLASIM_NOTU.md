# Paylaşım Notu — İçerik Yazarı Agent

**Mod:** C (şablona çevrildi — TAM JENERİK)

## Orijinal amaç → yeni jenerik çerçeve

Orijinal proje, belirli bir kişi için **tek bir nişte** (Dubai gayrimenkul
yatırımı) sosyal medya scriptleri üreten bir agent'ti. İçinde o kişinin gerçek
script arşivi, kişisel rakip listesi ve onun sesiyle yazılmış örnekler vardı.

Yeni çerçeve: **herhangi bir niş için, kişinin kendi sesine sadık içerik üreten
jenerik agent şablonu.** Niş, referans corpus ve üslup kuralları artık birer
placeholder — öğrenci kendi nişini tanımlayıp doldurur. Çekirdek desen
(referans corpus + skill anayasası + deterministik tool'lar + ilham listesi)
aynen korundu.

## Yapılan temizlik

### Kişisel veri scrub
- Kişi adı, sosyal medya handle'ları ve YouTube kanal linki — tüm dosyalardan çıkarıldı
- Niş bağlamı (sektöre özel emlak/yatırım konusu) README ve SKILL.md'den
  jenerikleştirildi; niş artık bir placeholder
- `tools/transcript.py` içindeki niş-spesifik user-agent → `IcerikYazariBot/1.0`
- `tools/calculator.py` docstring'indeki kişiye özel içerik ekibi referansı çıkarıldı

### Sahibin envanteri / corpus → şablona indirildi
- `reference-scripts/` altındaki 4 dosya (sahibin gerçek, telif'li script arşivi —
  bölge analizleri, gayrimenkul yatırımı, hesaplama, ilham scriptleri) **silindi**;
  yerine `_BOS_SABLON.md` konuldu (yapı + "buraya kendi corpus'unu koy" açıklaması)
- `rakipler.md` (sahibin gerçek rakip emlakçı listesi — 5 isim/handle) **boşaltıldı**;
  yerine 2 jenerik örnek satır + kullanım açıklaması kondu
- `SKILL.md` baştan yazıldı: niş-spesifik konsept kategorileri, format kuralları
  ve "kim için" bölümü jenerik şablona çevrildi

### Niş-spesifik tool
- `tools/calculator.py` bir Dubai gayrimenkul yatırım hesaplayıcısıydı. Silinmedi
  çünkü "agent rakam üretirken deterministik tool çağırır" desenini gösteriyor —
  ama docstring'i "bu bir örnek niş-spesifik araç, kendi nişine göre değiştir/sil"
  notuyla güncellendi
- `tools/currency.py` ve `tools/transcript.py` zaten jenerik — olduğu gibi kaldı

### Sırlar
- Koda gömülü sır bulunmadı
- `transcript.py` `SUPADATA_API_KEY`'i env'den okuyor — yeni `.env.example` eklendi

### Not
- README'de bahsedilen `.agent/workflows/` klasörü kaynak projede zaten yoktu;
  README bu referans olmadan yeniden yazıldı

## Öğrenci ne yapmalı

1. **Nişini tanımla** — `skills/icerik-yazari/SKILL.md` baştan sona örnek bir niş
   üzerinden yazılmış. Konsept kategorilerini, format ve üslup kurallarını kendi
   sektörüne göre yeniden yaz. Bu agent'in en kritik dosyası.
2. **Referans corpus'u doldur** — `reference-scripts/` boş şablonla geliyor.
   Kendi en iyi 5-15 script'ini buraya koy; agent senin tarzını bunlardan öğrenir.
3. **İlham listesini doldur** — `rakipler.md`'ye kendi nişindeki ilham hesaplarını ekle.
4. **Tool'ları uyarla** — `tools/calculator.py` örnek bir gayrimenkul hesaplayıcı;
   nişin farklıysa kendi mantığınla değiştir veya sil.
5. `.env.example` → `.env` kopyala, `SUPADATA_API_KEY`'i doldur (transkript aracı için).
