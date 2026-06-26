"""SESLI video birlestirme (concat a=1) + ffmpeg yardimcilari.

Recete kaynagi: _skills/kie-ai-video-production/pipelines/dinamik-coklu-video-birlestirme.md
(oradaki a=0 sessiz concat'in sesli versiyonu). Sessiz klipler anullsrc ile doldurulur,
cikti loudnorm ile YouTube seviyesine (-14 LUFS) cekilir.
"""

import json
import logging
import re
import shutil
import subprocess

logger = logging.getLogger("FFmpegAssembler")


def get_ffmpeg() -> str:
    """PATH'teki ffmpeg, yoksa imageio-ffmpeg binary'si."""
    path = shutil.which("ffmpeg")
    if path:
        return path
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def _run(cmd: list, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        tail = (result.stderr or "").strip().splitlines()[-8:]
        raise RuntimeError(f"ffmpeg komutu basarisiz (exit {result.returncode}): " + " | ".join(tail))
    return result


def probe(path: str) -> dict:
    """Klip metadata'si: {"duration_s", "width", "height", "has_audio"}.

    Once ffprobe (json), yoksa `ffmpeg -i` stderr parse (imageio-ffmpeg ffprobe icermez).
    """
    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        result = _run([
            ffprobe, "-v", "error", "-print_format", "json",
            "-show_format", "-show_streams", path,
        ])
        data = json.loads(result.stdout)
        duration_s = float(data.get("format", {}).get("duration", 0.0) or 0.0)
        width, height, has_audio = 0, 0, False
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video" and not width:
                width = int(stream.get("width", 0) or 0)
                height = int(stream.get("height", 0) or 0)
                if not duration_s and stream.get("duration"):
                    duration_s = float(stream["duration"])
            elif stream.get("codec_type") == "audio":
                has_audio = True
        return {"duration_s": duration_s, "width": width, "height": height, "has_audio": has_audio}

    # Fallback: ffmpeg -i cikti olmadan exit!=0 doner, stderr yine de metadata icerir
    result = _run([get_ffmpeg(), "-hide_banner", "-i", path], check=False)
    stderr = result.stderr or ""
    if "Invalid data" in stderr or "No such file" in stderr:
        raise RuntimeError(f"probe basarisiz: {path}: {stderr.strip().splitlines()[-1]}")

    duration_s = 0.0
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", stderr)
    if m:
        duration_s = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))

    width, height = 0, 0
    for line in stderr.splitlines():
        if "Video:" in line and "Stream" in line:
            dim = re.search(r"(\d{2,5})x(\d{2,5})", line)
            if dim:
                width, height = int(dim.group(1)), int(dim.group(2))
                break

    has_audio = bool(re.search(r"Stream #.*Audio:", stderr))
    return {"duration_s": duration_s, "width": width, "height": height, "has_audio": has_audio}


def assemble_episode(clip_paths: list, output_path: str, width: int = 1080,
                     height: int = 1920, fps: int = 24, loudnorm: bool = True) -> dict:
    """Klipleri SESLI concat eder (v=1:a=1) ve normalize edilmis tek mp4 uretir."""
    if not clip_paths:
        raise ValueError("assemble_episode: bos klip listesi")

    ffmpeg = get_ffmpeg()
    infos = [probe(p) for p in clip_paths]
    n = len(clip_paths)

    cmd = [ffmpeg, "-hide_banner", "-y"]
    for p in clip_paths:
        cmd += ["-i", p]

    # Sessiz klipler icin anullsrc girdileri klip girdilerinden SONRA eklenir;
    # audio_slot[i] = i. klibin sesinin geldigi input index'i
    audio_slot = []
    extra_idx = n
    for i, info in enumerate(infos):
        if info["has_audio"]:
            audio_slot.append(i)
        else:
            dur = max(info["duration_s"], 0.1)
            cmd += ["-f", "lavfi", "-t", f"{dur:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
            audio_slot.append(extra_idx)
            extra_idx += 1

    filters = []
    for i in range(n):
        filters.append(
            f"[{i}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps}[v{i}]"
        )
        filters.append(
            f"[{audio_slot[i]}:a]aresample=48000,"
            f"aformat=sample_fmts=fltp:channel_layouts=stereo[a{i}]"
        )

    pairs = "".join(f"[v{i}][a{i}]" for i in range(n))
    if loudnorm:
        filters.append(f"{pairs}concat=n={n}:v=1:a=1[outv][cata]")
        filters.append("[cata]loudnorm=I=-14:TP=-1.5:LRA=11[outa]")
    else:
        filters.append(f"{pairs}concat=n={n}:v=1:a=1[outv][outa]")

    cmd += [
        "-filter_complex", ";".join(filters),
        "-map", "[outv]", "-map", "[outa]",
        "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        output_path,
    ]

    logger.info(f"assemble_episode: {n} klip -> {output_path}")
    _run(cmd)
    return {"duration_s": probe(output_path)["duration_s"]}


def extract_frame(path: str, dest_path: str, t: float = 1.0) -> str:
    """t saniyesinden tek kare PNG cikarir (QC icin)."""
    _run([get_ffmpeg(), "-hide_banner", "-y", "-ss", f"{t:.3f}", "-i", path,
          "-frames:v", "1", dest_path])
    return dest_path


def _safe_drawtext(text: str) -> str:
    """drawtext icin guvenli metin (escape derdi olmayan karakterler)."""
    return re.sub(r"[^A-Za-z0-9 _.-]", "", text)[:40]


def make_placeholder_clip(dest_path: str, duration: int, with_audio: bool = True,
                          label: str = "") -> str:
    """DRY_RUN klibi: testsrc2 + (istenirse) 440Hz sinus sesi."""
    ffmpeg = get_ffmpeg()

    def build(with_label: bool) -> list:
        cmd = [ffmpeg, "-hide_banner", "-y",
               "-f", "lavfi", "-t", str(duration), "-i", "testsrc2=size=1080x1920:rate=24"]
        if with_audio:
            cmd += ["-f", "lavfi", "-t", str(duration), "-i",
                    "sine=frequency=440:sample_rate=48000"]
        if with_label:
            cmd += ["-vf", f"drawtext=text='{_safe_drawtext(label)}':fontcolor=white:"
                           f"fontsize=72:x=(w-text_w)/2:y=(h-text_h)/2"]
        cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p"]
        if with_audio:
            cmd += ["-c:a", "aac", "-b:a", "192k", "-ac", "2"]
        cmd += ["-shortest", dest_path]
        return cmd

    if label:
        try:
            _run(build(with_label=True))
            return dest_path
        except RuntimeError as e:
            logger.warning(f"drawtext basarisiz, labelsiz devam: {e}")
    _run(build(with_label=False))
    return dest_path


def make_placeholder_image(dest_path: str, text: str = "") -> str:
    """DRY_RUN gorseli: testsrc2 tek kare PNG."""
    ffmpeg = get_ffmpeg()

    def build(with_label: bool) -> list:
        cmd = [ffmpeg, "-hide_banner", "-y",
               "-f", "lavfi", "-i", "testsrc2=size=1080x1920:rate=24"]
        if with_label:
            cmd += ["-vf", f"drawtext=text='{_safe_drawtext(text)}':fontcolor=white:"
                           f"fontsize=72:x=(w-text_w)/2:y=(h-text_h)/2"]
        cmd += ["-frames:v", "1", dest_path]
        return cmd

    if text:
        try:
            _run(build(with_label=True))
            return dest_path
        except RuntimeError as e:
            logger.warning(f"drawtext basarisiz, metinsiz devam: {e}")
    _run(build(with_label=False))
    return dest_path
