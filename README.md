# Foto Kita Blur

Aplikasi kamera interaktif yang membuat tampilan blur saat pengguna menunjukkan gesture `PEACE`. Dibangun dengan MediaPipe + OpenCV, dilengkapi musik latar opsional.

## Fitur
- Blur realtime saat gesture `PEACE` terdeteksi.
- Overlay landmark tangan yang bisa dinyalakan/dimatikan.
- Musik latar otomatis loop jika `music.mp3` tersedia.
- Mute/unmute musik tanpa menghentikan aplikasi.
- Tampilan kamera mirror.

## Kebutuhan Sistem
- Python 3.11 - 3.14 (disarankan 3.12)
- Webcam
- Sistem audio (untuk musik)
- `make`
- OS: Linux/Windows/macOS

### Dependency
| Package | Versi |
|---|---|
| `numpy` | 2.3.5 |
| `opencv-contrib-python` | 4.14.0.94 |
| `mediapipe` | 0.10.35 |
| `pygame-ce` | 2.5.8 |

`pygame-ce` menyediakan modul `pygame` yang dipakai untuk pemutaran musik.

## Instalasi
```bash
make install
```

Atau manual:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Menjalankan
```bash
make run
```

Atau:
```bash
.venv/bin/python foto_blur.py
```

## Musik
- Taruh file `music.mp3` di root folder project.
- Musik akan diputar otomatis dan di-loop.
- Tekan `M` untuk mute/unmute.
- `music.mp3` tidak di-commit ke Git.
- Jika file tidak ada, aplikasi tetap berjalan tanpa musik.

## Kontrol
| Aksi | Fungsi |
|---|---|
| Tunjukkan `PEACE` | Aktifkan blur |
| `D` | Toggle overlay landmark |
| `M` | Mute/unmute musik |
| `ESC` | Keluar |

## Troubleshooting
- Kamera tidak bisa dibuka: tutup aplikasi yang memakai webcam (Discord, Zoom, Meet, browser).
- Cek aplikasi pemakai kamera: `fuser -v /dev/video0`.
- Musik `OFF`: pastikan `music.mp3` ada dan dependency sudah terinstall (`make install`).
- `ModuleNotFoundError`: jalankan `make install`.
- Setup bermasalah: jalankan `make reset && make install`.
- Tangan tidak stabil terdeteksi: pastikan pencahayaan cukup dan tangan terlihat penuh di kamera.
