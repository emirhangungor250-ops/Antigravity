"""
A/B test — merge_video_audio audio_volume karşılaştırması.

Karakterin sesinin ambient efektlere göre baskınlığını ayarlamak için
audio_volume parametresinin etkisini canlı Replicate API ile test eder.

Kullanım:
    REPLICATE_API_TOKEN=... python test_audio_volume_ab.py

Çıktı: 3 farklı volume seviyesinde merge edilmiş video URL'leri.
İndirip kulakla karşılaştır.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))

from services.replicate_service import ReplicateService

# Sample inputs:
# - Video: kısa Seedance ambient'li klip (test_videos/skincare.mp4 değil — onu yüklemek lazım;
#   bu yüzden public sample URL kullanıyoruz). Replicate accepts URI inputs.
# - Audio: kısa voice mp3
# Replicate'in kendi sample asset'leri çalışmıyorsa, e2e_result_*.json içinden raw_video_url
# ve audio_url okunabilir.

import json
from pathlib import Path


def load_sample_urls():
    """e2e_result jsonlarından gerçek raw video + audio URL'i bul."""
    for fname in ["e2e_result_skincare.json", "e2e_result_fashion.json", "e2e_result_tech.json"]:
        p = Path(__file__).parent / fname
        if not p.exists():
            continue
        d = json.loads(p.read_text())
        # e2e_result schema: top-level wrapper, içinde "result" dict'i
        r = d.get("result") if isinstance(d.get("result"), dict) else d
        raw = r.get("raw_video_url")
        au = r.get("audio_url")
        if raw and au:
            return raw, au
    return None, None


def main():
    token = os.environ.get("REPLICATE_API_TOKEN")
    if not token:
        print("ERROR: REPLICATE_API_TOKEN env var lazım")
        sys.exit(1)

    raw_video, audio_url = load_sample_urls()
    if not (raw_video and audio_url):
        print("UYARI: e2e_result jsonlarında raw_video_url + audio_url bulunamadı.")
        print("Bunun yerine elle URL ver (env: TEST_VIDEO_URL, TEST_AUDIO_URL)")
        raw_video = os.environ.get("TEST_VIDEO_URL")
        audio_url = os.environ.get("TEST_AUDIO_URL")
        if not (raw_video and audio_url):
            print("ERROR: TEST_VIDEO_URL + TEST_AUDIO_URL gerekli")
            sys.exit(1)

    print(f"Video: {raw_video[:80]}...")
    print(f"Audio: {audio_url[:80]}...")
    print()

    svc = ReplicateService(api_token=token)

    results = {}
    for vol in [1.0, 2.5, 3.5]:
        print(f"━━━ audio_volume={vol} ━━━")
        t0 = time.time()
        try:
            url = svc.merge_video_audio(
                video_url=raw_video,
                audio_url=audio_url,
                replace_audio=False,
                duration_mode="audio",
                audio_volume=vol,
            )
            elapsed = time.time() - t0
            results[vol] = url
            print(f"  → {url}")
            print(f"  ({elapsed:.1f}s)")
        except Exception as e:
            print(f"  HATA: {e}")
            results[vol] = f"ERROR: {e}"
        print()

    print("\n━━━ ÖZET ━━━")
    for vol, url in results.items():
        print(f"  audio_volume={vol}:  {url}")
    print("\nHer video'yu indir + kulakla karşılaştır.")
    print("Beklenen: 1.0 = voice ambient'in altında, 2.5 = voice baskın, 3.5 = voice çok baskın (clip riski).")


if __name__ == "__main__":
    main()
