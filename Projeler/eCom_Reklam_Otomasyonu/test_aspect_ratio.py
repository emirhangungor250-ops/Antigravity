"""Aspect ratio testleri — hem canlı API smoke test hem mock payload doğrulama."""
import os
import sys
import json
import requests
from unittest.mock import patch, MagicMock

API_KEY = os.environ.get("KIE_API_KEY", "")
BASE_URL = "https://api.kie.ai/api/v1"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}


def test_create_task(aspect_ratio: str, label: str = ""):
    """Test a single aspect_ratio value (CANLI API — KIE_API_KEY gerekli)."""
    if not API_KEY:
        print("KIE_API_KEY tanımsız — canlı test atlanıyor.")
        return
    payload = {
        "model": "bytedance/seedance-2",
        "input": {
            "prompt": "A simple red ball rolling on a table.",
            "duration": 5,
            "aspect_ratio": aspect_ratio,
            "generate_audio": False,
            "web_search": False,
        },
    }
    print(f"\n{'='*50}")
    print(f"Testing: '{aspect_ratio}' {label}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    try:
        resp = requests.post(
            f"{BASE_URL}/jobs/createTask",
            headers=HEADERS,
            json=payload,
            timeout=30,
        )
        print(f"HTTP Status: {resp.status_code}")
        data = resp.json()
        print(f"Response code: {data.get('code')}")
        print(f"Response msg: {data.get('msg')}")
        if data.get("code") == 200:
            task_id = data.get("data", {}).get("taskId", "?")
            print(f"OK SUCCESS - taskId: {task_id}")
        else:
            print(f"FAIL - code={data.get('code')}, msg={data.get('msg')}")
    except Exception as e:
        print(f"EXCEPTION: {e}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MOCK TESTLER — Reference image kombinasyonu
# Kullanıcının seçtiği aspect_ratio'nun referans görsel varken bile
# payload'a doğru gittiğini doğrular (eskiden "adaptive" override ediyordu).
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _make_mock_kie_service(api_key: str = "test-key"):
    from services.kie_api import KieAIService
    svc = KieAIService(api_key=api_key)
    # _create_task ve upload_file_from_url mock'la
    svc._create_task = MagicMock(return_value="mock-task-id")
    # upload_file_from_url Kie-native gibi davransın - URL'yi olduğu gibi döndür
    svc.upload_file_from_url = MagicMock(side_effect=lambda url: url)
    return svc


def test_aspect_with_reference_image_916():
    """9:16 + reference image → payload aspect_ratio='9:16' olmalı (NOT 'adaptive')."""
    svc = _make_mock_kie_service()
    svc.create_video(
        prompt="test prompt",
        duration=5,
        aspect_ratio="9:16",
        reference_images=["https://example.com/ref-portrait.jpg"],
    )
    payload = svc._create_task.call_args[0][0]
    actual = payload["input"]["aspect_ratio"]
    assert actual == "9:16", f"9:16 ref ile beklenen '9:16', alındı '{actual}'"
    print(f"OK 9:16 + reference → payload aspect_ratio='{actual}' (override yok)")


def test_aspect_with_reference_image_169():
    """16:9 + reference image → payload aspect_ratio='16:9' olmalı."""
    svc = _make_mock_kie_service()
    svc.create_video(
        prompt="test prompt",
        duration=5,
        aspect_ratio="16:9",
        reference_images=["https://example.com/ref-landscape.jpg"],
    )
    payload = svc._create_task.call_args[0][0]
    actual = payload["input"]["aspect_ratio"]
    assert actual == "16:9", f"16:9 ref ile beklenen '16:9', alındı '{actual}'"
    print(f"OK 16:9 + reference → payload aspect_ratio='{actual}' (override yok)")


def test_aspect_with_first_frame_url():
    """first_frame_url + 9:16 → payload aspect_ratio='9:16' olmalı."""
    svc = _make_mock_kie_service()
    svc.create_video(
        prompt="test prompt",
        duration=5,
        aspect_ratio="9:16",
        first_frame_url="https://example.com/first-frame.jpg",
    )
    payload = svc._create_task.call_args[0][0]
    actual = payload["input"]["aspect_ratio"]
    assert actual == "9:16", f"first_frame ile beklenen '9:16', alındı '{actual}'"
    print(f"OK first_frame_url + 9:16 → payload aspect_ratio='{actual}'")


def test_aspect_no_reference():
    """Referans yok + 1:1 → payload aspect_ratio='1:1' olmalı (normalize geçmeli)."""
    svc = _make_mock_kie_service()
    svc.create_video(
        prompt="test prompt",
        duration=5,
        aspect_ratio="1:1",
    )
    payload = svc._create_task.call_args[0][0]
    actual = payload["input"]["aspect_ratio"]
    assert actual == "1:1", f"referanssız 1:1 ile beklenen '1:1', alındı '{actual}'"
    print(f"OK no reference + 1:1 → payload aspect_ratio='{actual}'")


def run_mock_tests():
    print("\n" + "="*50)
    print("MOCK TESTLER — Reference image + aspect ratio")
    print("="*50)
    test_aspect_with_reference_image_916()
    test_aspect_with_reference_image_169()
    test_aspect_with_first_frame_url()
    test_aspect_no_reference()
    print("\nTüm mock testler geçti.")


if __name__ == "__main__":
    # Mock testler (offline) - her zaman çalışır
    run_mock_tests()

    # Canlı API testleri - sadece KIE_API_KEY ve --live flag varsa
    if "--live" in sys.argv and API_KEY:
        for ratio in ["9:16", "16:9", "1:1", "4:3", "3:4", "21:9"]:
            test_create_task(ratio, "(expected valid)")
        test_create_task("9/16", "(invalid separator)")
        test_create_task("vertical", "(invalid label)")
