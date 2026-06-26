"""
Canlı A/B test — gerçek video + gerçek ElevenLabs voice ile merge.

Yerel test_videos/skincare.mp4'ü Replicate'a yükler, taze TR voice üretir,
3 farklı audio_volume seviyesinde merge eder. Çıktı: 3 indirilebilir URL.
"""
import io
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))

from services.replicate_service import ReplicateService
from services.elevenlabs_service import ElevenLabsService

VOICE_TEXT = (
    "Bu üründe asıl fark cilt bariyerini gerçekten onarıyor olmasıdır. "
    "İlk haftada parlaklığı görmen kuvvetle muhtemel."
)


def main():
    rep_token = os.environ.get("REPLICATE_API_TOKEN")
    el_token = os.environ.get("ELEVENLABS_API_KEY")
    if not (rep_token and el_token):
        print("ERROR: REPLICATE_API_TOKEN + ELEVENLABS_API_KEY gerekli")
        sys.exit(1)

    rep = ReplicateService(api_token=rep_token)
    el = ElevenLabsService(api_key=el_token)

    # 1) Voice üret
    print("ElevenLabs TTS...")
    audio_bytes = el.generate_speech(text=VOICE_TEXT, voice_name="Ahu")
    dur = ElevenLabsService.measure_audio_duration(audio_bytes)
    print(f"  voice süresi: {dur:.2f}s, {len(audio_bytes)} bytes")

    # 2) Audio upload
    audio_url = rep.upload_audio(audio_bytes, filename="ab_test_voice.mp3")
    print(f"  audio_url: {audio_url[:90]}")

    # 3) Video upload
    print("Video upload...")
    video_path = os.path.join(os.path.dirname(__file__), "test_videos", "skincare.mp4")
    with open(video_path, "rb") as f:
        video_bytes = f.read()
    file_obj = io.BytesIO(video_bytes)
    uploaded = rep.client.files.create(file_obj, filename="ab_test_video.mp4")
    video_url = uploaded.urls.get("get") if hasattr(uploaded, "urls") else str(uploaded)
    video_url = str(video_url)
    print(f"  video_url: {video_url[:90]}")

    # 4) Üç farklı seviyede merge
    results = {}
    for vol in [1.0, 2.5, 3.5]:
        print(f"\n━━━ audio_volume={vol} ━━━")
        t0 = time.time()
        try:
            url = rep.merge_video_audio(
                video_url=video_url,
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

    print("\n━━━ ÖZET ━━━")
    for vol, url in results.items():
        print(f"  audio_volume={vol}:  {url}")
    print(
        "\nHer video'yu indir + kulakla karşılaştır.\n"
        "Beklenen: 1.0 = voice ambient'e karışıyor, 2.5 = voice baskın net,\n"
        "3.5 = voice çok baskın (clip riski olabilir)."
    )


if __name__ == "__main__":
    main()
