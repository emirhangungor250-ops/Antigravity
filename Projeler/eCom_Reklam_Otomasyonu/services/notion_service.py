from __future__ import annotations

"""
Notion Service — Üretim Logları
=================================
eCom Reklam Otomasyonu üretim loglarını Notion'a yazar.
Database: NOTION_DB env değişkeninden gelir (constructor'a geçirilir).
"""

from datetime import datetime, timezone

from notion_client import Client as NotionClient

from logger import get_logger

log = get_logger("notion_service")


class NotionService:
    """Notion API ile üretim loglama."""

    def __init__(self, token: str, database_id: str):
        self.client = NotionClient(auth=token)
        self.database_id = database_id

    def health_check(self) -> tuple[bool, str]:
        """Notion DB'ye lightweight bir sorgu at, erişilebilirliği doğrula.

        Returns:
            (ok, message). ok=False ise message kullanıcıya gösterilebilir
            hatadır. Tek admin bot startup'ında sessiz fail yerine bilinçli
            log üretir (üretim sırasında "neden Notion log yok" sorularını
            önler).
        """
        try:
            self.client.databases.retrieve(database_id=self.database_id)
            return True, "ok"
        except Exception as exc:
            err = str(exc)[:200]
            log.error(f"Notion health check başarısız: {err}", exc_info=True)
            return False, err

    def log_production(
        self,
        brand: str,
        product: str,
        concept: str,
        video_duration: int,
        aspect_ratio: str,
        resolution: str,
        language: str,
        estimated_cost: float,
        status: str,
        video_url: str = "",
        error_message: str = "",
        user_name: str = "",
    ) -> str | None:
        """
        Üretim logunu Notion database'ine yazar.

        Args:
            brand: Marka adı
            product: Ürün adı
            concept: Reklam konsepti
            video_duration: Video süresi (saniye)
            aspect_ratio: En/boy oranı
            resolution: Çözünürlük
            language: Dil (Türkçe/İngilizce)
            estimated_cost: Tahmini maliyet ($)
            status: Durum (Üretiliyor, Tamamlandı, Hata)
            video_url: Video URL (tamamlandığında)
            error_message: Hata mesajı (başarısız olursa)
            user_name: Telegram kullanıcı adı

        Returns:
            str | None: Notion page URL veya None (hata durumunda)
        """
        try:
            properties = {
                "Proje": {"title": [{"text": {"content": f"eCom — {brand}"}}]},
                "Marka": {"rich_text": [{"text": {"content": brand}}]},
                "Ürün": {"rich_text": [{"text": {"content": product}}]},
                "Konsept": {"rich_text": [{"text": {"content": concept[:2000]}}]},
                "Video Süresi (s)": {"number": video_duration},
                "Aspect Ratio": {"select": {"name": aspect_ratio}},
                "Çözünürlük": {"select": {"name": resolution}},
                "Dil": {"select": {"name": language}},
                "Tahmini Maliyet ($)": {"number": estimated_cost},
                "Durum": {"select": {"name": status}},
                "Tarih": {"date": {"start": datetime.now(timezone.utc).isoformat()}},
            }

            # Opsiyonel alanlar
            if video_url:
                properties["Video URL"] = {"url": video_url}
            if error_message:
                properties["Hata Mesajı"] = {
                    "rich_text": [{"text": {"content": error_message[:2000]}}]
                }
            if user_name:
                properties["Kullanıcı"] = {
                    "rich_text": [{"text": {"content": user_name}}]
                }

            page = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties,
            )

            page_url = page.get("url", "")
            log.info(f"Notion log oluşturuldu: {brand} — {status} → {page_url}")
            return page_url

        except Exception:
            log.error(f"Notion loglama hatası: {brand}", exc_info=True)
            return None

    def update_production_status(
        self,
        page_id: str,
        status: str,
        video_url: str = "",
        error_message: str = "",
        estimated_cost: float | None = None,
    ) -> bool:
        """
        Mevcut bir üretim logunun durumunu günceller.

        Args:
            page_id: Notion page ID
            status: Yeni durum
            video_url: Video URL (tamamlandığında)
            error_message: Hata mesajı (başarısız olursa)
            estimated_cost: Güncellenmiş maliyet (sahne sayısı değiştiyse)

        Returns:
            bool: Güncelleme başarılı mı
        """
        try:
            properties = {
                "Durum": {"select": {"name": status}},
            }

            if video_url:
                properties["Video URL"] = {"url": video_url}
            if error_message:
                properties["Hata Mesajı"] = {
                    "rich_text": [{"text": {"content": error_message[:2000]}}]
                }
            if estimated_cost is not None:
                properties["Tahmini Maliyet ($)"] = {"number": float(estimated_cost)}

            self.client.pages.update(
                page_id=page_id,
                properties=properties,
            )

            log.info(f"Notion log güncellendi: {page_id} → {status}")
            return True

        except Exception:
            log.error(f"Notion güncelleme hatası: {page_id}", exc_info=True)
            return False

    def log_social_posting(
        self,
        page_id: str,
        platforms: list[str],
        post_results: dict,
        status: str,
    ) -> bool:
        """Bir Notion page'ine sosyal medya paylaşım sonucunu COMMENT olarak yazar.

        Production page'inin "Hata Mesajı" / "Durum" alanlarına dokunmaz —
        bu alanlar üretim hatası ve üretim durumu için ayrılmıştır.
        Sosyal medya post URL'leri page comment'i olarak görünür; Notion'da
        page açıldığında discussion panelinde okunabilir.

        Args:
            page_id: Notion page ID (production log)
            platforms: Hedeflenen platform listesi (sıralı)
            post_results: {platform: {url|post_url, video_id, ...}}
            status: Etiket (örn. "Paylaşıldı", "Kısmi", "Hata")
        """
        try:
            comment_lines = [f"📤 Sosyal Medya — {status}: {', '.join(platforms)}"]
            for platform, info in (post_results or {}).items():
                url = ""
                if isinstance(info, dict):
                    url = info.get("url") or info.get("post_url") or info.get("video_url") or ""
                if url:
                    comment_lines.append(f"• {platform}: {url}")
                else:
                    comment_lines.append(f"• {platform}: (link yok)")
            comment_text = "\n".join(comment_lines)[:1900]

            self.client.comments.create(
                parent={"page_id": page_id},
                rich_text=[{"type": "text", "text": {"content": comment_text}}],
            )
            log.info(f"Notion social comment: page={page_id} platforms={platforms} status={status}")
            return True

        except Exception:
            log.error(f"Notion social log hatası: {page_id}", exc_info=True)
            return False
