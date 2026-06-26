# 🔐 Merkezi Credential Deposu

Bu klasör Antigravity ekosistemindeki **tüm API token ve bağlantılarını** merkezi olarak yönetir.

## Dosyalar

| Dosya | İçerik | Güvenlik |
|-------|--------|----------|
| `master.env.example` | Tüm API anahtarlarının şablonu | ✅ Şablon — kopyalanabilir |
| `master.env` | Gerçek API anahtarlarınız (`.env` formatı) | 🔒 .gitignore — siz oluşturursunuz |
| `google-service-account.json` | Google Cloud Service Account | 🔒 .gitignore — siz eklersiniz |
| `oauth/google_auth.py` | Merkezi Google OAuth modülü | ✅ Kullanılabilir |
| `oauth/auth_helper.py` | İlk seferlik OAuth yetkilendirme | ✅ Kullanılabilir |
| `oauth/gmail-*-token.json` | OAuth token dosyaları | 🔒 .gitignore — siz oluşturursunuz |

## İlk Kurulum

1. `master.env.example` dosyasını `master.env` olarak kopyalayın
2. İçindeki `<...>` placeholder'larını kendi API anahtarlarınızla doldurun
3. `master.env` dosyası `.gitignore` ile korunur — asla GitHub'a gitmez

## Google OAuth — Merkezi Token Yönetimi

### Yapı
```
oauth/
├── google_auth.py              ← TÜM projeler bu modülü kullanır
├── auth_helper.py              ← İlk seferlik yetkilendirme (bir daha gerekmez)
├── gmail-account1-token.json   ← İlk hesabınızın token'ı (siz oluşturursunuz)
└── gmail-account2-token.json   ← İkinci hesabınızın token'ı (opsiyonel)
```

### İlk Kurulum (Token Üretme)
```bash
cd oauth
python3 auth_helper.py account1   # tarayıcı açılır, Google ile giriş yaparsınız
```

Token bir kez üretilir, `refresh_token` içerir → sonsuza kadar otomatik yenilenir.
Google Cloud Console'da uygulamayı silmediğiniz sürece tarayıcı tekrar açılmaz.

### Kullanım (Projelerden)
```python
import sys
sys.path.insert(0, '_knowledge/credentials/oauth')
from google_auth import get_gmail_service, get_sheets_service

gmail = get_gmail_service("account1")
sheets = get_sheets_service("account1")
```

### Token Scope'ları
- `gmail.modify` — Gmail okuma, yazma, gönderme
- `gmail.send` — Gmail gönderme
- `drive.file` — Google Drive dosya erişimi
- `spreadsheets` — Google Sheets okuma/yazma

## Kurallar

- ⚠️ Bu klasördeki gerçek credential dosyalarını **asla** GitHub'a push etmeyin
- 🔄 Token değiştiğinde **sadece `master.env`** dosyasını güncelleyin
- 🔑 Google OAuth sorun çıkarırsa: `cd oauth && python3 auth_helper.py status`
- 📋 Yeni servis eklendiğinde `master.env` ve `api-anahtarlari.md` dosyalarını güncelleyin
