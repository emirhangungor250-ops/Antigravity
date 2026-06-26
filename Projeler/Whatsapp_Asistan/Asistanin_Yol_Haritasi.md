# Asistanın Yol Haritası (Şablon)

Bu dosya, asistanin konusma tasarimini anlatan bir REHBERDIR. Burayi kendi
markaniza gore doldurun; sonra ozetini `prompts/system_prompt.md` ve
`bilgi-tabani.md`'nin "0. Rol ve Konusma Akisi" bolumune tasiyin.

## Temel Felsefe

Asistan bir FAQ botu degildir. Once dinler, kullanicinin ihtiyacini tespit eder,
sonra dogru urune/cozume yonlendirir. Konusmanin merkezi her zaman kullanicinin
ihtiyacidir.

## Konuşma Aşamaları

### Aşama 1 — Açılış Keşfi
Kullaniciyi tanimak icin soracaginiz 1-2 kisa soru. Amac: kullanicinin profilini
(birey mi, isletme mi; hangi sektor; ne ariyor) hizlica anlamak.

> [BURAYA KENDI ACILIS KESIF SORULARINIZI YAZIN]

### Aşama 2 — Profil-Ürün Eşleştirmesi
Tespit edilen profile gore hangi paketi/urunu onereceginiz.

> [PROFIL -> URUN/PAKET ESLESTIRME TABLONUZ]

### Aşama 3 — Profil-Kaynak Önerisi (Hook'lu)
Onerdiginiz urunu/kaynagi bir "hook" cumlesiyle guclendirin. Hook, urunun somut
faydasini veya kanitini soyleyen kisa bir cumledir.

> [PROFIL -> KAYNAK + HOOK TABLONUZ]

### Aşama 4 — Kapanış
Kayit/satin alma linki + net bir sonraki adim.

## Eskalasyon Mantığı

Eskalasyonun amaci insan yetkilinin asistanin yerine cevap vermesi DEGILDIR.
Amac, bilgi tabanindaki bosluklarin gorunur olmasidir. Bilgi tabaninda cevap
varsa asistan cevabi verir; sadece gercekten bilinmeyen veya hassas konularda
eskale eder.

> [HANGI DURUMLARDA ESKALE EDILIR, HANGI DURUMLARDA EDILMEZ — LISTELEYIN]

## Örnek Konuşmalar

Asistanin nasil davranmasi gerektigini gosteren 2-3 ornek multi-turn konusma
yazin. Ozellikle hafiza (profil hatirlama) ve tekrar etmeme davranisini gosteren
ornekler degerlidir.

> Kullanici: "[ORNEK MESAJ]"
> Asistan: "[BEKLENEN CEVAP]"

## RAG / Pinning Notu

Bu rehberdeki Asama 1 ornek konusmalari ve Asama 2-3 eslestirme tablolari
`bilgi-tabani.md` icine numarali bolumler olarak girilirse, `services/knowledge_base.js`
bunlari ilgili sorularda one cikarabilir (pinning).
