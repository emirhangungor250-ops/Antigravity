# 🚀 Antigravity Starter Kit — Başlangıç Rehberi

Hoş geldiniz. Bu paket, hazır AI otomasyonları, skill'ler ve agent'larla dolu bir
çalışma ortamıdır. Amacı: sıfırdan başlamak yerine, çalışan örneklerin üzerine kendi
işinizi kurmanız.

Bu pakette **API anahtarı veya kişisel veri yoktur**. Her şey sizin kendi
bilgilerinizle dolduracağınız placeholder'lar (`<...>`) halindedir.

---

## Antigravity nedir, nasıl çalışır

Antigravity, Claude Code ile birlikte çalışan bir **mono-repo**'dur. Dört katmandan oluşur:

- **`Projeler/`** — Hazır otomasyon projeleri (Telegram botları, içerik üretim pipeline'ları, lead toplama araçları, web siteleri). Bunları kendi işinize uyarlarsınız.
- **`_skills/`** — Yeniden kullanılabilir yetenekler (video üretimi, e-posta gönderimi, lead generation vb.). Projeler bunları çağırır.
- **`_agents/`** — Çok adımlı işleri uçtan uca yöneten orkestratör agent'lar.
- **`_knowledge/`** — Sizin profiliniz, API anahtarlarınız, çalışma kurallarınız. Antigravity her konuşmada buraya bakar.

---

## İlk 3 Adım

### 1. Kendinizi tanıtın
`_knowledge/profil.md` dosyasını açın ve kendinizle ilgili bölümleri doldurun.
Antigravity sizi buradan tanır — kim olduğunuzu, ne ürettiğinizi, nasıl çalışmak istediğinizi.

### 2. API anahtarlarınızı girin
- `_knowledge/credentials/master.env.example` dosyasını `master.env` olarak kopyalayın.
- İçindeki `<...>` placeholder'larını kendi API anahtarlarınızla doldurun.
- Hangi servisin ne işe yaradığını `_knowledge/api-anahtarlari.md` dosyasında görebilirsiniz.
- Sadece kullanacağınız servislerin anahtarlarını girmeniz yeterli — hepsini doldurmak zorunda değilsiniz.

### 3. Bir proje seçip çalıştırın
`Projeler/` altındaki bir projeyi açın. Her projenin içinde:
- `README.md` — projenin ne yaptığı ve nasıl çalıştığı
- `.env.example` — o projenin ihtiyaç duyduğu ayarlar
- `_PAYLASIM_NOTU.md` — bu projenin paket için nasıl hazırlandığı, neyi değiştirmeniz gerektiği

`.env.example` dosyasını `.env` olarak kopyalayıp doldurun, sonra projeyi çalıştırın.

---

## ⚠️ Güvenlik Uyarısı

Bu paketi GitHub'a veya başka bir yere yüklerseniz:

- **`master.env`, `.env` ve `credentials/` içindeki dosyalar ASLA push edilmemeli.**
- Kök dizindeki `.gitignore` dosyası bunları otomatik korur — silmeyin.
- Bir projeyi paylaşmadan önce kendi API anahtarlarınızı temizlediğinizden emin olun.
- API anahtarlarınız sızarsa, ilgili servisten hemen yenisini üretip eskisini iptal edin.

---

## Skill'ler nasıl çalışır

Skill'lere dokunmanıza gerek yok. Çoğu, anahtarları `_knowledge/api-anahtarlari.md`
veya `master.env` üzerinden okur. Siz anahtarlarınızı girince skill'ler çalışır hale gelir.
Bir skill'i tetiklemek için Claude Code'a ne istediğinizi söylemeniz yeterli.

## Yeni proje / skill nasıl eklenir

`CLAUDE.md` dosyasındaki "Yeni Proje Açma Check-list" bölümüne bakın. Kısaca:
yeni bir klasör açın, `.env.example` + `README.md` yazın, bağımlılıkları tanımlayın,
gerekiyorsa `railway.json` ekleyin. Antigravity bu adımlarda size yardımcı olur.

---

İyi çalışmalar. Takıldığınız yerde Claude Code'a sorun — bu ortam tam da bunun için var.
