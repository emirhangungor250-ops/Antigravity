"""LLM beyninin yapisal cikti kontratlari.

Bu semalar Anthropic structured outputs (client.messages.parse) ile kullanilir.
API limitlerini kodlayan kisitlar (maks 3 karakter/sahne, duration enum, ≤120 char
example_dialogue) buradadir — degistirmeden once Gemini Omni API limitlerine bak.
"""
from typing import List, Literal
from pydantic import BaseModel, Field, field_validator

# Gemini Omni'nin 30 preset sesi → cinsiyet haritasi (bible dogrulamasinda kullanilir)
VOICE_PRESET_GENDERS = {
    "achernar": "F", "achird": "M", "algenib": "M", "algieba": "M", "alnilam": "M",
    "aoede": "F", "autonoe": "F", "callirrhoe": "F", "charon": "M", "despina": "F",
    "enceladus": "M", "erinome": "F", "fenrir": "M", "gacrux": "F", "iapetus": "M",
    "kore": "F", "laomedeia": "F", "leda": "F", "orus": "M", "puck": "M",
    "pulcherrima": "N", "rasalgethi": "M", "sadachbia": "M", "sadaltager": "M",
    "schedar": "M", "sulafat": "F", "umbriel": "M", "vindemiatrix": "F",
    "zephyr": "F", "zubenelgenubi": "M",
}

VoicePreset = Literal[
    "achernar", "achird", "algenib", "algieba", "alnilam", "aoede", "autonoe",
    "callirrhoe", "charon", "despina", "enceladus", "erinome", "fenrir", "gacrux",
    "iapetus", "kore", "laomedeia", "leda", "orus", "puck", "pulcherrima",
    "rasalgethi", "sadachbia", "sadaltager", "schedar", "sulafat", "umbriel",
    "vindemiatrix", "zephyr", "zubenelgenubi",
]


# ─── Dizi Kitabi (BiblePlan) ──────────────────────────────────────────────

class VoiceSpec(BaseModel):
    preset: VoicePreset
    voice_description: str = Field(description="English; timbre, pace, emotion, quirks. Must include 'Speaks natural conversational Turkish.'")
    example_dialogue_tr: str = Field(max_length=110, description="Karakteristik tek Türkçe replik")


class CharacterSpec(BaseModel):
    id: str = Field(description="snake_case slug, ör. kemal_amca")
    name: str
    age: int
    role: str
    personality: str
    speaking_style: str
    visual_description: str = Field(description="English full-body portrait spec incl. WARDROBE LOCK (one outfit, garment by garment)")
    voice: VoiceSpec


class NarratorSpec(BaseModel):
    enabled: bool
    preset: str = Field(description="Voice preset name if enabled, else empty string")
    voice_description: str
    example_dialogue_tr: str = Field(max_length=110)


class EnvironmentSpec(BaseModel):
    id: str
    name_tr: str
    image_prompt: str = Field(description="English; EMPTY location plate, no people, vertical 9:16, fixed time of day")
    lighting_signature: str = Field(description="Short English phrase reused in every scene set here")
    time_of_day: str


class PropSpec(BaseModel):
    id: str
    name_tr: str
    image_prompt: str = Field(description="English; object isolated on neutral surface, no hands, no text")
    story_role: str


class ArtStyle(BaseModel):
    style_paragraph: str = Field(description="50-100 English words, checklist-prose: medium, palette (3-4 named colors), lighting, lens/DoF, texture, mood")
    style_board_prompt: str = Field(description="Abstract mood frame of main environment, NO characters")
    negative_constraints: List[str]


class SeriesArc(BaseModel):
    central_question_tr: str
    episode_seeds_tr: List[str] = Field(min_length=8, max_length=8, description="8 bölümlük eskalasyon arkı, her biri tek cümle Türkçe")


class BiblePlan(BaseModel):
    title_tr: str
    logline_tr: str
    tone: List[str]
    series_seed: int = Field(ge=10000, le=99999)
    characters: List[CharacterSpec] = Field(min_length=1, max_length=4)
    narrator: NarratorSpec
    environments: List[EnvironmentSpec] = Field(min_length=2, max_length=4)
    props: List[PropSpec] = Field(max_length=4)
    art_style: ArtStyle
    series_arc: SeriesArc


def validate_bible_plan(plan: BiblePlan) -> List[str]:
    """Pydantic'in yakalayamadigi semantik kurallar. Bos liste = gecerli."""
    errors = []
    presets = [c.voice.preset for c in plan.characters]
    if len(presets) != len(set(presets)):
        errors.append("Two characters share the same voice preset — each must be unique.")
    if plan.narrator.enabled:
        if plan.narrator.preset not in VOICE_PRESET_GENDERS:
            errors.append(f"Narrator preset '{plan.narrator.preset}' is not a valid voice preset.")
        elif plan.narrator.preset in presets:
            errors.append("Narrator voice preset is already used by a character.")
    ids = [c.id for c in plan.characters] + [e.id for e in plan.environments] + [p.id for p in plan.props]
    if len(ids) != len(set(ids)):
        errors.append("Duplicate ids across characters/environments/props.")
    return errors


# ─── Bölüm Senaryosu (EpisodeScript) ──────────────────────────────────────

class DialogueLine(BaseModel):
    speaker: str = Field(description="Character id present in the scene, or 'NARRATOR'")
    line_tr: str = Field(description="Natural spoken Turkish, max 15 words, no em-dashes")
    delivery_en: str = Field(description="2-5 English words: tone of delivery")


class SceneSpec(BaseModel):
    scene_number: int
    duration_s: Literal[4, 6, 8, 10]
    environment_id: str
    character_ids: List[str] = Field(max_length=3)
    prop_ids: List[str] = Field(max_length=2)
    action: str = Field(description="English, 25-60 words, present tense, ONE primary action, strong verbs, NO appearance description")
    camera: str = Field(description="One shot size + one movement, subject and camera motion described separately")
    lighting: str = Field(description="Must incorporate the environment's lighting_signature")
    dialogue: List[DialogueLine] = Field(max_length=3)
    sfx: str = Field(description="1-2 specific diegetic sounds. NEVER music.")
    continuity_from_previous: str = Field(description="ONE short English sentence: what the viewer just saw")
    emotional_beat: str


class MemoryUpdate(BaseModel):
    synopsis_short_tr: str = Field(description="40-60 kelime Türkçe bölüm özeti")
    cliffhanger_tr: str
    threads_opened: List[str]
    threads_resolved: List[str]
    character_developments: List[str]
    new_canon_facts: List[str]


class YouTubeMeta(BaseModel):
    title_tr: str = Field(description="Maks 60 karakter, bir emoji, merak boşluğu")
    description_tr: str
    tags: List[str] = Field(max_length=12)


class EpisodeScript(BaseModel):
    episode_number: int
    title_tr: str
    synopsis_tr: str
    hook_description: str
    cliffhanger_description: str
    music_mood: str = Field(description="Episode-level hint; clips themselves contain no music")
    scenes: List[SceneSpec] = Field(min_length=6, max_length=10)
    memory_update: MemoryUpdate
    youtube: YouTubeMeta

    @field_validator("scenes")
    @classmethod
    def first_scene_is_hook(cls, v):
        if v and v[0].duration_s != 4:
            v[0].duration_s = 4  # hook her zaman 4sn — sessizce onar
        return v


# ─── Yardimci yapisal ciktilar ────────────────────────────────────────────

class SimplifiedPrompt(BaseModel):
    prompt: str = Field(description="Content-policy-safe rewrite of the scene prompt, same story beat")


class SeasonSummary(BaseModel):
    summary_tr: str = Field(description="≤200 kelime, tüm kanon gerçekler korunarak")


class QCVerdict(BaseModel):
    character_match: bool
    expected_count_visible: bool
    has_text_artifacts: bool
    style_consistent: bool
    note: str
