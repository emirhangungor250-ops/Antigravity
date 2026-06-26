# Paylasim Notu — eposta-gonderim

**Mod:** A (+ ornek scriptler sablonlandi)

## Ne yapildi
- `token.json` ve `credentials.json` — gercek OAuth kimlik dosyalari; pakete dahil edilmedi.
- `send_swc.py` — gercek alici eposta/isimleri + marka + kisisel imza iceriyordu; jenerik outreach sablonuna cevrildi.
- `scripts/mass_send_english.py` — hardcoded CSV yollari + gercek marka/imza iceriyordu; jenerik sablona cevrildi, yollar relative yapildi.
- `SKILL.md` — hardcoded gonderici Gmail adresi jenerik ifadeyle degistirildi.

## Ogrenci ne yapmali
- Merkezi Google OAuth token kurulumu yapin (`_knowledge/credentials/oauth/`).
- `send_swc.py` / `mass_send_english.py` icindeki `<GONDEREN_ADI>`, `<MARKA_ADI>` ve alici listelerini kendi kampanyaniza gore doldurun.
