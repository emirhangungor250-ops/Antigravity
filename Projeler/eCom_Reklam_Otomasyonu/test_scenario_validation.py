"""Hızlı validasyon testi — scenario_engine quality issues fix'leri için.

Çalıştırma: cd Projeler/eCom_Reklam_Otomasyonu && python test_scenario_validation.py
"""
from core.scenario_engine import ScenarioEngine


def _base_scenario(**overrides):
    """5-sahnelik valid bir scenario template (issue üretmesin)."""
    base = {
        "narrative_hook": "Sabah aynaya bakınca yeni bir şey hissettim",
        "voiceover_text": "Bir sabah aynaya baktım ve farkı gördüm.",
        "character_gender": "kadın",
        "voice_name": "Ahu",
        "character_visual_prompt": "Genç kadın, doğal makyaj, banyoda ayna önünde.",
        "narrative_pattern": "before_after",
        "character_visual_prompt_before": "yorgun bakış",
        "character_visual_prompt_after": "parlak cilt",
        "scenes": [
            {"video_prompt": "Sahne 1", "voiceover_segment": "İki hafta önce", "duration_seconds": 5},
            {"video_prompt": "Sahne 2", "voiceover_segment": "Cildim çok kuruydu", "duration_seconds": 5},
            {"video_prompt": "Sahne 3", "voiceover_segment": "Bu kremi denedim", "duration_seconds": 5},
            {"video_prompt": "Sahne 4", "voiceover_segment": "Şimdi farkı görüyorum", "duration_seconds": 5},
        ],
    }
    base.update(overrides)
    return base


def test_voice_gender_lookup():
    assert ScenarioEngine._voice_gender("Ahu") == "kadın"
    assert ScenarioEngine._voice_gender("Adam") == "erkek"
    assert ScenarioEngine._voice_gender("İrem") == "kadın"
    assert ScenarioEngine._voice_gender("Filiz") == "kadın"
    assert ScenarioEngine._voice_gender("Nisa") == "kadın"
    assert ScenarioEngine._voice_gender("RandomVoice") == "unknown"
    assert ScenarioEngine._voice_gender("") == "unknown"
    print("OK voice_gender lookup")


def test_gender_mismatch_detected():
    # erkek karakter + kadın ses
    sc = _base_scenario(character_gender="erkek", voice_name="Ahu")
    issues = ScenarioEngine._scenario_quality_issues(sc)
    assert any("Cinsiyet uyumsuz" in i for i in issues), f"mismatch yakalanmadı: {issues}"
    print("OK gender mismatch detected")


def test_gender_match_no_issue():
    sc = _base_scenario(character_gender="kadın", voice_name="Ahu")
    issues = ScenarioEngine._scenario_quality_issues(sc)
    assert not any("Cinsiyet uyumsuz" in i for i in issues), f"yanlış flag: {issues}"
    print("OK gender match no issue")


def test_unknown_voice_no_mismatch():
    sc = _base_scenario(character_gender="erkek", voice_name="UnknownVoice123")
    issues = ScenarioEngine._scenario_quality_issues(sc)
    assert not any("Cinsiyet uyumsuz" in i for i in issues), f"unknown ses mismatch saymamalı: {issues}"
    print("OK unknown voice not flagged")


def test_short_hook_chars_detected():
    sc = _base_scenario(narrative_hook="ya")
    issues = ScenarioEngine._scenario_quality_issues(sc)
    assert any("karakter" in i.lower() or "çok kısa" in i.lower() for i in issues), \
        f"kısa hook yakalanmadı: {issues}"
    print("OK short hook (chars) detected")


def test_empty_hook_detected():
    sc = _base_scenario(narrative_hook="")
    issues = ScenarioEngine._scenario_quality_issues(sc)
    assert any("narrative_hook boş" in i for i in issues), f"boş hook yakalanmadı: {issues}"
    print("OK empty hook detected")


if __name__ == "__main__":
    test_voice_gender_lookup()
    test_gender_mismatch_detected()
    test_gender_match_no_issue()
    test_unknown_voice_no_mismatch()
    test_short_hook_chars_detected()
    test_empty_hook_detected()
    print("\nTüm testler geçti.")
