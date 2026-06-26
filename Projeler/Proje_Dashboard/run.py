"""Proje Dashboard orkestratör.

5 view: Bugün (default) + İş Çıktıları + Para + Bekleyen + Otomasyon.
Tüm collector'ları çalıştırır, view-bazlı veri yapısı üretir, HTML render eder.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent
ANTIGRAVITY_ROOT = ROOT.parent.parent
sys.path.insert(0, str(ROOT))

from collectors import railway as railway_collector
from collectors import routines as routines_collector
from collectors import signals as signals_collector
from collectors import subscriptions as subscriptions_collector
from collectors import notion_collector
from collectors import elevenlabs_collector
from collectors import hunter_collector
from collectors import firecrawl_collector
from collectors import apify_collector
from collectors import openai_collector
from collectors import anthropic_collector
from collectors import replicate_collector
from collectors import manychat_collector

LIVE_PROVIDER_MAP = {
    "elevenlabs": "ElevenLabs (TTS)",
    "hunter": "Hunter.io",
    "firecrawl": "Firecrawl",
    "apify": "Apify",
    "replicate": "Replicate",
    "manychat": "ManyChat",
}

# Para sekmesi — "amaca göre gruplama" kategorileri
CATEGORY_META = {
    "ai_beyin": {"label": "AI beyin", "icon": "🧠", "desc": "Düşünen, yazan AI motorları"},
    "uretim": {"label": "Görsel & video üretimi", "icon": "🎬", "desc": "Kapak, video, ses üretimi"},
    "arastirma": {"label": "Araştırma & scraping", "icon": "🔍", "desc": "Web scraping, lead bulma"},
    "altyapi": {"label": "Altyapı & yayın", "icon": "⚙️", "desc": "Barındırma, yayın, mail, mesajlaşma"},
}

# Kalemin category alanı yoksa provider'dan türet
PROVIDER_CATEGORY = {
    "anthropic": "ai_beyin", "openai": "ai_beyin", "perplexity": "ai_beyin",
    "kie": "uretim", "replicate": "uretim", "elevenlabs": "uretim",
    "apify": "arastirma", "firecrawl": "arastirma", "hunter": "arastirma",
    "railway": "altyapi", "typefully": "altyapi", "notion": "altyapi",
    "netlify": "altyapi", "resend": "altyapi", "manychat": "altyapi",
}


def safe(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        return {"ok": False, "error": str(e)}


def time_ago(iso_str: str | None) -> str:
    if not iso_str:
        return "bilinmiyor"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - dt
        total_seconds = int(delta.total_seconds())
        if total_seconds < 60:
            return "az önce"
        if total_seconds < 3600:
            return f"{total_seconds // 60} dk önce"
        if total_seconds < 86400:
            return f"{total_seconds // 3600} sa önce"
        days = delta.days
        if days < 30:
            return f"{days} gün önce"
        if days < 365:
            return f"{days // 30} ay önce"
        return f"{days // 365} yıl önce"
    except Exception:
        return iso_str[:10]


def status_class(status: str | None) -> str:
    if not status:
        return "unknown"
    s = status.upper()
    if s == "SUCCESS":
        return "success"
    if s in {"FAILED", "CRASHED"}:
        return "failed"
    if s in {"BUILDING", "DEPLOYING", "INITIALIZING"}:
        return "building"
    if s == "SKIPPED":
        return "skipped"
    return "unknown"


def build_bugun(notion: dict, railway: dict, signals: dict, para: dict) -> dict:
    today_rows = []
    uretim_bugun = 0
    onay_bekleyen = 0

    if notion.get("ok"):
        for it in notion.get("items", []):
            if not it.get("ok"):
                continue
            if it.get("new_today", 0) > 0:
                today_rows.append(
                    {
                        "kind": "Notion",
                        "where": it["label"],
                        "desc": f"{it['new_today']} yeni kayıt eklendi",
                        "count": it["new_today"],
                    }
                )
                uretim_bugun += it["new_today"]
            # Onay bekleyen draftlar — "fikir" havuzu sayılmaz (sürekli vardır)
            sc = it.get("status_counts") or {}
            draft_keys = [
                k for k in sc.keys()
                if any(d in k.lower() for d in ["draft", "pending", "onay", "yayına hazır"])
            ]
            onay_bekleyen += sum(sc.get(k, 0) for k in draft_keys)

    kirik_servis = 0
    kirik_servis_adlari = []
    toplam_servis = 0
    if railway.get("ok"):
        for s in railway.get("services", []):
            toplam_servis += 1
            dep = s.get("latest_deployment") or {}
            if (dep.get("status") or "").upper() in {"FAILED", "CRASHED"}:
                kirik_servis += 1
                kirik_servis_adlari.append(s.get("service_name") or "?")
    saglam_servis = toplam_servis - kirik_servis

    uretim_detay_parts = []
    if notion.get("ok"):
        for it in notion.get("items", []):
            if it.get("new_today", 0) > 0:
                uretim_detay_parts.append(f"{it['label']} +{it['new_today']}")
    uretim_detay = ", ".join(uretim_detay_parts[:3]) or "Bugün yeni kayıt yok"

    # Nabız panelinin eşik değerleri
    URETIM_HEDEF = 10  # günlük makul içerik üretim hedefi
    ONAY_ESIK = 5      # bu sayıyı geçince onay birikmesi sayılır

    return {
        "uretim_bugun": uretim_bugun,
        "uretim_detay": uretim_detay,
        "onay_bekleyen": onay_bekleyen,
        "kirik_servis": kirik_servis,
        "kirik_servis_adlari": kirik_servis_adlari,
        "aylik_toplam": para.get("grand_total", 0),
        "today_rows": today_rows,
        "kpi_alert": kirik_servis + (1 if onay_bekleyen > 5 else 0),
        # Sistem Nabzı paneli
        "nabiz": {
            "uretim": {
                "bugun": uretim_bugun,
                "hedef": URETIM_HEDEF,
                "pct": min(100, round(uretim_bugun / URETIM_HEDEF * 100)) if URETIM_HEDEF else 0,
            },
            "onaylar": {
                "bekleyen": onay_bekleyen,
                "esik": ONAY_ESIK,
                "pct": min(100, round(onay_bekleyen / ONAY_ESIK * 100)) if ONAY_ESIK else 0,
                "asti": onay_bekleyen > ONAY_ESIK,
            },
            "servisler": {
                "saglam": saglam_servis,
                "toplam": toplam_servis,
                "kirik": kirik_servis,
            },
            "para": {
                "tutar": para.get("grand_total", 0),
                "yon": "notr",  # geçmiş snapshot tutulmuyor; ileride trend eklenebilir
            },
        },
    }


def build_is_ciktilari(notion: dict, railway: dict) -> dict:
    return {
        "notion": [it for it in notion.get("items", []) if it.get("ok")] if notion.get("ok") else [],
        "servisler": _railway_service_list(railway),
    }


def _railway_service_list(railway: dict) -> list[dict]:
    if not railway.get("ok"):
        return []
    out = []
    for svc in railway.get("services", []):
        dep = svc.get("latest_deployment") or {}
        out.append(
            {
                "display_name": svc.get("service_name"),
                "monthly_usd": svc.get("monthly_usd", 0.0),
                "deploy_status": dep.get("status") or "—",
                "deploy_age": time_ago(dep.get("createdAt")),
                "status_class": status_class(dep.get("status")),
            }
        )
    return out


def build_para(subs: dict, railway: dict, live_collectors: list[dict]) -> dict:
    """live_collectors: ElevenLabs, Hunter, Firecrawl, Apify gibi canlı çekilenler.
    Manuel `ai_usage_estimates` kalemlerini override eder, source='live' işaretler.
    """
    fixed = list(subs.get("fixed", [])) if subs.get("ok") else []
    ai_usage = [dict(x) for x in subs.get("ai_usage", [])] if subs.get("ok") else []
    for item in ai_usage:
        item["source"] = "manual"
        item["live_note"] = None

    # Live override
    # Collector iki sınıfa ayrılır:
    #   1) "USD biliyor" (monthly_usd_known=True): ElevenLabs, Hunter, Firecrawl,
    #      Apify, OpenAI, Anthropic → tutar 0 bile olsa manuel tahmin override edilir.
    #   2) "Sadece sağlık" (False): Replicate, ManyChat, Kie → tier/note ek olarak
    #      gösterilir, manuel tahmin korunur (source='manual+health').
    live_by_provider = {c["provider"]: c for c in live_collectors if c.get("ok")}
    matched_keys = set()
    for item in ai_usage:
        p = item.get("provider")
        if p in live_by_provider:
            live = live_by_provider[p]
            live_usd = float(live.get("monthly_usd") or 0)
            known = bool(live.get("monthly_usd_known"))
            if known:
                item["monthly_usd"] = live_usd
                item["source"] = "live"
            else:
                item["source"] = "manual+health"
            item["live_note"] = live.get("note")
            item["tier"] = live.get("tier")
            item["usage_pct"] = live.get("usage_pct")
            matched_keys.add(p)

    # Live'da olup manuel listede olmayanları ekle (sadece USD bilen)
    for p, live in live_by_provider.items():
        if p in matched_keys:
            continue
        if not live.get("monthly_usd_known"):
            continue  # sağlık-bilgisi collector'ları yeni satır olarak ekleme
        ai_usage.append(
            {
                "name": live["name"],
                "provider": p,
                "monthly_usd": float(live.get("monthly_usd") or 0),
                "source": "live",
                "live_note": live.get("note"),
                "used_by": [],
                "console_url": live.get("console_url"),
                "tier": live.get("tier"),
            }
        )

    # fixed kalemlerine source işareti (kategori rozetleri için)
    for f in fixed:
        f["source"] = "sabit"

    fixed_total = round(sum(float(x.get("monthly_usd") or 0) for x in fixed), 2)
    ai_total = round(sum(float(x.get("monthly_usd") or 0) for x in ai_usage), 2)
    railway_official = railway.get("official_current_usd", 0) if railway.get("ok") else 0
    grand_total = round(fixed_total + ai_total + railway_official, 2)

    live_count = sum(1 for x in ai_usage if x.get("source") == "live")
    manual_count = len(ai_usage) - live_count

    period = railway.get("billing_period", {}) if railway.get("ok") else {}
    railway_services_total = 0.0
    if railway.get("ok"):
        railway_services_total = round(
            sum(float(s.get("monthly_usd") or 0) for s in railway.get("services", [])),
            2,
        )
    railway_delta = round(railway_official - railway_services_total, 2)

    categories = _build_categories(fixed, ai_usage, railway_official, railway)

    return {
        "grand_total": grand_total,
        "fixed_total": fixed_total,
        "ai_total": ai_total,
        "railway_official": railway_official,
        "railway_services_total": railway_services_total,
        "railway_delta": railway_delta,
        "fixed": fixed,
        "ai_usage": ai_usage,
        "categories": categories,
        "live_count": live_count,
        "manual_count": manual_count,
        "railway_invoices": railway.get("invoices", []) if railway.get("ok") else [],
        "railway_period_start": (period.get("start") or "")[:10],
        "railway_period_end": (period.get("end") or "")[:10],
    }


def _category_for(item: dict) -> str:
    """Kalemin kategorisini belirle: önce explicit `category`, sonra provider haritası."""
    cat = item.get("category")
    if cat in CATEGORY_META:
        return cat
    prov = item.get("provider")
    return PROVIDER_CATEGORY.get(prov, "altyapi")


def _build_categories(fixed: list, ai_usage: list, railway_official: float, railway: dict) -> list:
    """Tüm masraf kalemlerini amaca göre kategorilere böler.

    Her kategori: {key, label, icon, desc, total_usd, items}.
    Railway resmi tutarı altyapı kategorisine tek kalem olarak girer.
    Kategoriler harcamaya göre azalan sıralanır; boş kategori atlanır.
    """
    cats = {
        k: {"key": k, "total_usd": 0.0, "items": [], **CATEGORY_META[k]}
        for k in CATEGORY_META
    }

    for item in list(fixed) + list(ai_usage):
        ckey = _category_for(item)
        cats[ckey]["items"].append(item)
        cats[ckey]["total_usd"] += float(item.get("monthly_usd") or 0)

    # Railway tek kalem — gerçek fatura tutarı
    rw_svc_count = len(railway.get("services", [])) if railway.get("ok") else 0
    cats["altyapi"]["items"].append({
        "name": "Railway",
        "provider": "railway",
        "monthly_usd": railway_official,
        "source": "live",
        "note": f"{rw_svc_count} servis · gerçek fatura tutarı" if rw_svc_count else "gerçek fatura tutarı",
        "console_url": "https://railway.app/account/usage",
        "used_by": [],
    })
    cats["altyapi"]["total_usd"] += float(railway_official or 0)

    out = []
    for c in cats.values():
        if not c["items"]:
            continue
        c["total_usd"] = round(c["total_usd"], 2)
        c["items"].sort(key=lambda x: float(x.get("monthly_usd") or 0), reverse=True)
        out.append(c)
    out.sort(key=lambda c: c["total_usd"], reverse=True)
    return out


REASON_LABELS = {
    "failed": "Hata",
    "handover": "Handover",
    "deploy_yok": "Deploy yok",
    "yarim": "Yarım",
    "doc_eksik": "Doc",
}


def _brief_for(kind: str, project: str, desc: str, raw: dict) -> str:
    """Bekleyen item için Claude Code'a yapıştırılacak prompt."""
    if kind == "failed":
        return (
            f"Proje dashboard'umda **{project}** servisi CRASHED görünüyor (Railway). "
            f"Detay: {desc}. Kontrol et: bu servis hâlâ kullanılıyor mu? "
            "Kullanılıyorsa hatayı çöz ve redeploy et. "
            "Eğer arşiv adayıysa Railway'den sil ve `_arsiv/`'e taşı."
        )
    if kind == "handover":
        fname = raw.get("file", "")
        return (
            f"Proje dashboard'umda kökte duran **{fname}** dosyası bekleyen olarak görünüyor. "
            "İçeriği oku, içindeki tüm maddeler uygulanmış mı kontrol et. "
            "Tamamı uygulandıysa dosyayı sil. Uygulanmayan madde varsa bana net liste ver."
        )
    if kind == "deploy_yok":
        return (
            f"Proje dashboard'umda **{project}** projesi deploy edilmemiş görünüyor (.env.example var ama Railway'de servis yok). "
            "Bu projenin ne durumda olduğunu anla: "
            "(1) aktif geliştirme paused mi → `config/ignored_signals.yaml`'a ekle, "
            "(2) deploy edilmeye hazır mı → deploy et, "
            "(3) arşiv adayı mı → `_arsiv/`'e taşı. "
            "Karar ver ve uygula."
        )
    if kind == "yarim":
        return (
            f"Proje dashboard'umda **{project}**'in README'sinde 'TODO/BEKLİYOR/PENDING' geçiyor. "
            f"İlgili satır: '{desc}'. README'yi oku, hâlâ yapılması gereken bir şey kalmışsa yap. "
            "Tamamlanmışsa README'yi temizle. Karar verirsen `ignored_signals.yaml`'a da ekleyebilirsin."
        )
    if kind == "doc_eksik":
        return (
            f"Proje dashboard'umda **{project}**'in dokümantasyon dosyası (Sistem_Nasil_Calisir.html) eksik. "
            "Projeyi açıklayan bir doküman üret."
        )
    return f"Proje dashboard'umda **{project}** için '{kind}' tipinde sinyal var. Detay: {desc}. Kontrol et ve çöz."


# Her sinyal tipi için sade Türkçe cümle + buton aksiyonu.
# Teknik etiketler (deploy_yok, yarim...) artık UI'da görünmez.
def _cumle_for(kind: str, project: str, desc: str) -> tuple[str, str]:
    """(cumle, aksiyon) döner — sade dille ne durumda + ne yapılmalı."""
    if kind == "failed":
        return (f"{project} servisi çökmüş, şu an çalışmıyor.", "Düzelt")
    if kind == "handover":
        return (f"{project} — bir devir notu bekliyor. İçindeki işler "
                "tamamlandı mı kontrol edilmeli.", "Kontrol et")
    if kind == "deploy_yok":
        return (f"{project} projesi henüz yayına alınmamış. Ya bitirilip "
                "deploy edilmeli ya da arşive kaldırılmalı.", "Karar ver")
    if kind == "yarim":
        return (f"{project} yarım kalmış görünüyor — notlarında "
                "bekleyen iş var.", "Karar ver")
    if kind == "doc_eksik":
        return (f"{project} için sistem-anlatım dokümanı eksik.", "Üret")
    return (f"{project}: {desc}", "İncele")


def build_bekleyen(signals: dict, notion: dict) -> dict:
    out = []
    if signals.get("ok"):
        for s in signals.get("signals", []):
            kind = s["kind"]
            if kind == "handover":
                project = s.get("project_hint", s.get("file", ""))
                desc = s.get("first_line") or s.get("file")
            elif kind == "failed":
                project = f"{s.get('project')} / {s.get('service')}"
                desc = f"Son deploy: {s.get('status')} · {time_ago(s.get('deployment_time'))}"
            elif kind == "deploy_yok":
                project = s.get("project")
                desc = s.get("folder", "")
            elif kind == "yarim":
                project = s.get("project")
                desc = s.get("sample", "")
            elif kind == "doc_eksik":
                project = s.get("project")
                desc = "Sistem_Nasil_Calisir.html eksik"
            else:
                project = s.get("project", "?")
                desc = ""
            brief = _brief_for(kind, project, desc, s)
            cumle, aksiyon = _cumle_for(kind, project, desc)
            out.append(
                {
                    "kind": kind,
                    "label": REASON_LABELS.get(kind, kind),
                    "project": project,
                    "desc": desc,
                    "cumle": cumle,
                    "aksiyon": aksiyon,
                    "brief": brief,
                    "link": None,
                }
            )

    # Notion'dan onay bekleyenleri ekle
    if notion.get("ok"):
        for it in notion.get("items", []):
            if not it.get("ok"):
                continue
            sc = it.get("status_counts") or {}
            notion_url = it.get("notion_url")
            for status_name, count in sc.items():
                low = status_name.lower()
                if not any(k in low for k in ["pending", "draft", "yayına hazır", "failed"]):
                    continue
                if count <= 0:
                    continue
                is_failed = "failed" in low
                label = "Hata" if is_failed else "Draft"
                kind = "failed" if is_failed else "yarim"
                desc = f"{count} kayıt '{status_name}' — Notion DB'sinde inceleme bekliyor"
                if is_failed:
                    cumle = f"{it['label']} listesinde {count} kayıt hata almış ('{status_name}')."
                    aksiyon = "Düzelt"
                    brief = (
                        f"Proje dashboard'umda **{it['label']}** Notion DB'sinde "
                        f"{count} kayıt '{status_name}' durumunda. "
                        f"Açıp neden hata aldıklarını anla, düzelt veya iptal et. "
                        f"DB linki: {notion_url or '(yok)'}"
                    )
                    link = None
                else:
                    cumle = f"{it['label']} listesinde {count} kayıt onayını bekliyor ('{status_name}')."
                    aksiyon = "İncele"
                    brief = (
                        f"Proje dashboard'umda **{it['label']}** Notion DB'sinde "
                        f"{count} kayıt '{status_name}' durumunda — onay bekliyor. "
                        f"Açıp her birini incele: onayla veya iptal et. "
                        f"DB linki: {notion_url or '(yok)'}"
                    )
                    link = notion_url
                out.append(
                    {
                        "kind": kind,
                        "label": label,
                        "project": f"{it['label']}",
                        "desc": desc,
                        "cumle": cumle,
                        "aksiyon": aksiyon,
                        "brief": brief,
                        "link": link,
                    }
                )

    return {"count": len(out), "all": out, "top5": out[:5]}


def build_otomasyon(routines: dict, railway: dict) -> dict:
    """Otomasyon filosu view'i — cloud routine takvimi + Railway servis sağlık şeridi."""
    railway_svc = []
    if railway.get("ok"):
        for svc in railway.get("services", []):
            dep = svc.get("latest_deployment") or {}
            cls = status_class(dep.get("status"))
            renk = {"success": "yesil", "failed": "kirmizi", "building": "sari"}.get(cls, "gri")
            railway_svc.append({
                "ad": svc.get("service_name"),
                "renk": renk,
            })
    railway_svc.sort(key=lambda s: s["ad"] or "")

    rw_ozet = {"yesil": 0, "sari": 0, "kirmizi": 0, "gri": 0}
    for s in railway_svc:
        rw_ozet[s["renk"]] = rw_ozet.get(s["renk"], 0) + 1

    if routines.get("ok"):
        out = dict(routines)
    else:
        out = {"ok": False, "error": routines.get("error", "routines collector hatası")}
    out["railway_servisler"] = railway_svc
    out["railway_ozet"] = rw_ozet
    return out


def render_dashboard(state: dict) -> str:
    env = Environment(
        loader=FileSystemLoader(str(ROOT / "render")),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("template.html")

    bugun = build_bugun(state["notion"], state["railway"], state["signals"], state["para"])
    is_ciktilari = build_is_ciktilari(state["notion"], state["railway"])
    para = state["para"]
    bekleyen = build_bekleyen(state["signals"], state["notion"])
    otomasyon = build_otomasyon(state["routines"], state["railway"])

    return template.render(
        today_str=datetime.now().strftime("%d %B %Y, %A"),
        generated_at=datetime.now().strftime("%H:%M"),
        bugun=bugun,
        is_ciktilari=is_ciktilari,
        para=para,
        bekleyen=bekleyen,
        otomasyon=otomasyon,
    )


def _rotate_log(path: Path, max_bytes: int = 10 * 1024 * 1024) -> None:
    """Log dosyası 10MB'ı geçtiyse .1'e taşı, eskisini sil."""
    try:
        if path.exists() and path.stat().st_size > max_bytes:
            backup = path.with_suffix(path.suffix + ".1")
            if backup.exists():
                backup.unlink()
            path.rename(backup)
    except Exception:
        pass


def main():
    for nm in ("launchagent.log", "launchagent.err"):
        _rotate_log(ROOT / "data" / nm)

    print("→ Railway billing + servisler...")
    railway = safe(railway_collector.collect)
    if railway.get("ok"):
        print(f"  ✓ resmi=${railway.get('official_current_usd', 0)} tahmin=${railway.get('estimated_total_usd', 0)} servis={len(railway.get('services', []))}")
    else:
        print(f"  ✗ {railway.get('error')}")

    print("→ Notion DB'leri...")
    notion = safe(notion_collector.collect)
    if notion.get("ok"):
        print(f"  ✓ {notion.get('ok_count', 0)}/{notion.get('total_count', 0)} DB")

    print("→ Sinyaller...")
    signals = safe(signals_collector.collect, railway.get("services", []))
    if signals.get("ok"):
        print(f"  ✓ {len(signals.get('signals', []))} sinyal")

    print("→ Otomasyon filosu (routines)...")
    routines = safe(routines_collector.collect)
    if routines.get("ok"):
        oz = routines.get("ozet", {})
        print(f"  ✓ {routines.get('toplam', 0)} routine — {oz.get('yesil',0)} sağlıklı, {oz.get('sari',0)} gecikmiş, {oz.get('kirmizi',0)} ölü")
        if routines.get("kayitsiz"):
            print(f"  ⚠️ Kayıtsız routine log'u: {routines['kayitsiz']}")
    else:
        print(f"  ✗ {routines.get('error')}")

    print("→ Abonelikler...")
    subs = safe(subscriptions_collector.collect)
    if subs.get("ok"):
        print(f"  ✓ sabit=${subs.get('fixed_total_usd', 0)} AI manuel=${subs.get('ai_total_usd', 0)}")

    print("→ Canlı API maliyetleri çekiliyor...")
    live_collectors = []
    pending_setup = []
    for label, mod, provider_key in [
        ("ElevenLabs", elevenlabs_collector, "elevenlabs"),
        ("Hunter", hunter_collector, "hunter"),
        ("Firecrawl", firecrawl_collector, "firecrawl"),
        ("Apify", apify_collector, "apify"),
        ("OpenAI", openai_collector, "openai"),
        ("Anthropic API", anthropic_collector, "anthropic"),
        ("Replicate", replicate_collector, "replicate"),
        ("ManyChat", manychat_collector, "manychat"),
    ]:
        r = safe(mod.collect)
        if r.get("ok"):
            r["provider"] = provider_key
            live_collectors.append(r)
            print(f"  ✓ {label:14s} ${r['monthly_usd']:.2f} [{r.get('tier','?')}]")
        else:
            pending_setup.append({"name": label, "error": r.get("error", "")})
            print(f"  ✗ {label:14s} {r.get('error', '')}")

    para = build_para(subs, railway, live_collectors)
    print(f"→ Aylık toplam: ${para['grand_total']} (canlı {para['live_count']} + manuel {para['manual_count']})")

    state = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "railway": railway,
        "notion": notion,
        "signals": signals,
        "routines": routines,
        "subscriptions": subs,
        "live_collectors": live_collectors,
        "para": para,
    }

    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "state.json").write_text(json.dumps(state, indent=2, default=str))

    print("→ HTML render...")
    html = render_dashboard(state)
    output_path = ROOT / "proje-dashboard.html"
    output_path.write_text(html)
    print(f"  ↓ {output_path}")

    root_link = ANTIGRAVITY_ROOT / "proje-dashboard.html"
    if root_link.exists() or root_link.is_symlink():
        root_link.unlink()
    try:
        root_link.symlink_to(output_path)
    except OSError:
        root_link.write_text(html)

    print("\nTamam. Açmak için:")
    print("  open proje-dashboard.html")


if __name__ == "__main__":
    main()
