# Paylaşım Notu — sifre-yonetici

**Mod:** A

**Ne yapıldı:**
- `SKILL.md`: kişisel e-postalar `<EMAIL>` placeholder'ına çevrildi. Kişiye özel servis adı "İkincil" yapıldı.
- `scripts/env_manager.py`: servis tespit pattern'lerinden kişisel e-posta/domain regex'leri kaldırıldı; sadece env var adı pattern'leri kaldı.
- Gerçek API key VALUE'su bulunmadı — dosya yalnızca `master.env` yapısını anlatıyor.

**Öğrenci ne yapmalı:** `_knowledge/credentials/master.env` dosyasını kendi anahtarlarıyla doldur. Skill, projelerin ihtiyaçlarını otomatik analiz edip `.env` üretir.
