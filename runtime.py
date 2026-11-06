"""Explicit input, portable fonts and checked media output. No network access."""
import os
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path


def input_path(value=None):
    value = value or os.environ.get('TAIEX_INPUT_CSV')
    if not value:
        raise ValueError('Provide --data YOUR_AUTHORIZED.csv or set TAIEX_INPUT_CSV. No full historical dataset is bundled.')
    path = Path(value).expanduser()
    if not path.is_file():
        raise ValueError(f'Input CSV does not exist: {path}')
    return path


@lru_cache(maxsize=4)
def font_path(kind, configured):
    value = os.environ.get('TAIEX_CJK_FONT' if kind == 'cjk' else 'TAIEX_LATIN_FONT')
    if value:
        path = Path(value).expanduser()
        if not path.is_file():
            raise ValueError(f'Configured {kind} font does not exist: {path}')
        return str(path)
    if Path(configured).is_file():
        return configured
    if shutil.which('fc-match'):
        found = subprocess.run(['fc-match', '-f', '%{file}', configured], capture_output=True, text=True, check=True).stdout
        if Path(found).is_file():
            # Fontconfig silently substitutes missing families; require a real CJK family.
            family = subprocess.run(['fc-match', '-f', '%{family}', configured], capture_output=True, text=True, check=True).stdout
            if kind == 'cjk' and not any(word in family.lower() for word in ['cjk', 'noto sans tc', 'source han', 'hei', 'pingfang', 'gothic', 'ming']):
                raise ValueError('Install a Traditional Chinese font or set TAIEX_CJK_FONT and TAIEX_CJK_FACE_INDEX.')
            return found
    raise ValueError('Install Noto Sans CJK and DejaVu Sans with fontconfig, or set TAIEX_CJK_FONT and TAIEX_LATIN_FONT to installed font files.')


def require_ffmpeg():
    found = shutil.which('ffmpeg')
    if not found:
        raise ValueError('FFmpeg is required on PATH for video export; it is not bundled.')
    return found


def encode_frames(frame_fn, output, duration, fps=30, start=0, size=(720, 1280)):
    if duration <= 0 or fps <= 0 or start < 0:
        raise ValueError('Duration and FPS must be positive; start must be nonnegative.')
    count = round(duration * fps)
    if count < 1:
        raise ValueError('Requested duration is shorter than one frame.')
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [require_ffmpeg(), '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pixel_format', 'rgb24', '-video_size', f'{size[0]}x{size[1]}', '-framerate', str(fps), '-i', '-', '-an', '-c:v', 'libx264', '-preset', 'fast', '-threads', '2', '-crf', '18', '-pix_fmt', 'yuv420p', str(output)]
    proc = subprocess.Popen(command, stdin=subprocess.PIPE)
    try:
        for index in range(count):
            frame = frame_fn(start + index / fps)
            if frame.size != size or frame.mode != 'RGB':
                raise ValueError('Frame must be RGB at the configured output size.')
            proc.stdin.write(frame.tobytes())
        proc.stdin.close()
        result = proc.wait()
        if result:
            raise RuntimeError(f'FFmpeg encoder failed with status {result}')
    except BaseException:
        if proc.poll() is None:
            proc.terminate()
        proc.wait()
        raise
    return count / fps


def mux_audio(silent, wav, output):
    subprocess.run([require_ffmpeg(), '-y', '-loglevel', 'error', '-i', str(silent), '-i', str(wav), '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-shortest', str(output)], check=True)
