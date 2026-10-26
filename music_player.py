import time
from pathlib import Path


class MusicPlayer:
    def __init__(self, path="music.mp3", volume=50):
        self.path = Path(path)
        self.volume = max(0, min(100, int(volume)))
        self.available = False
        self.muted = False
        self.message = ""
        self._pygame = None
        self._mixer = None

        if not self.path.exists():
            self.message = f"{self.path.name} tidak ditemukan"
            return

        try:
            import pygame

            self._pygame = pygame
            pygame.mixer.init()
            self._mixer = pygame.mixer.music
            self._mixer.load(str(self.path))
            self._mixer.set_volume(self.volume / 100.0)
            self._mixer.play(loops=-1)
            time.sleep(0.1)
            self.available = True
        except Exception as exc:
            self.message = f"musik gagal dimulai: {exc}"
            self.available = False

    def toggle_mute(self):
        if not self.available or self._mixer is None or self._pygame is None:
            return self.muted
        if self.muted:
            self._mixer.set_volume(self.volume / 100.0)
            self.muted = False
        else:
            self._mixer.set_volume(0.0)
            self.muted = True
        return self.muted

    def status_text(self):
        if self.muted:
            return "MUSIC MUTED"
        if self.available:
            return "MUSIC ON"
        return "MUSIC OFF"

    def close(self):
        try:
            if self._mixer is not None:
                self._mixer.stop()
        except Exception:
            pass
        try:
            if self._pygame is not None:
                self._pygame.mixer.quit()
        except Exception:
            pass
        finally:
            self.available = False
            self._mixer = None
            self._pygame = None
