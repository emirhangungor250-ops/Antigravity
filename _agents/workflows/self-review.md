---
description: Self-Review — veri yazan/okuyan görevlerden sonra çıktıyı kaynaktan doğrula. "Yaptım" yerine "Doğruladım" de.
---

# /self-review — Sonuç Doğrulama

> **Altın kural:** "Yaptım" yerine "Doğruladım: X."
> Veri yazan/okuyan her görevden sonra ZORUNLU çalışır — slash çağırılmasa bile.

## Ne Zaman?

Sheets/Notion/Gmail/Calendar/GitHub'a yazma, pipeline çalıştırma, veri dönüştürme — kısaca dış sistemde sonuç bırakan her iş.

## 5 Adım

### 1) Beklenti
- Bu görev NE üretmeliydi? (örn. "47 lead Notion'a")
- Çıktı NEREDE olmalı?
- KAÇ kayıt/öğe?

### 2) Kaynağı Oku
Kaynak sistemden (Sheets / Notion / Gmail) kayıt sayısını ve örnek içeriği TEKRAR çek.

### 3) Hedefi Oku
Yazdığın yeri **gerçekten** sorgula:
- **Notion** → `mcp_notion-mcp-server_API-query-data-source` (sorts: created_time desc)
- **Sheets** → `read_sheet_values`
- **Gmail** → `search_gmail_messages` (`in:sent`)
- **GitHub** → `get_file_contents`

Her kayıtta zorunlu alanlar dolu mu? "İsimsiz Lead" problemi var mı?

### 4) Karşılaştır
- Kaynak sayısı = Hedef sayısı? **(zorunlu eşitlik)**
- İlk 3 + son 3 kaydı içerikle karşılaştır.
- Duplicate, boş alan, format hatası (tarih/sayı) var mı?

### 5) Karar + Rapor

✅ Şartlar: sayı eşit + zorunlu alanlar dolu + örnekleme geçti + duplicate yok.
❌ Tek biri sağlanmazsa → tanımla, düzelt, ADIM 2'ye dön. Döngü temizlenene kadar devam.

**Kullanıcıya çıktı:**
```
✅ Self-Review
Kaynak: [sistem] · X kayıt
Hedef:  [sistem] · X kayıt
Eşleşme: %100 · Boş alan: yok · Örnekleme: 3/3
```

## ⛔ Yapma

- "Başarıyla tamamlandı" deyip kontrol etmemek.
- API 200 dönmesini yeterli saymak.
- "N kayıt işlendi" log'una güvenmek (gerçekten yazıldı mı?).
- Kullanıcının kendisinin doğrulamasını beklemek — **SEN** doğrula.
