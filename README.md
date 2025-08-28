# RTMP Client (PySide6 + FFmpeg)

RTMP client universal untuk live stream menggunakan Python + PySide6 (Qt) dan backend FFmpeg yang dijalankan via subprocess. Cross‑platform: Windows, macOS, Linux.

## Fitur Minimum (MVP)
- Input file video (MP4/MKV/MOV)
- Input RTMP URL (YouTube, TikTok, Facebook, Twitch)
- Tombol Start/Stop untuk menjalankan/menghentikan proses FFmpeg
- Log output FFmpeg di GUI

FFmpeg command dasar yang dipakai:
```
ffmpeg -re -i <video_file> -c:v libx264 -preset veryfast -b:v 2500k \
       -c:a aac -ar 44100 -b:a 128k -f flv <rtmp_url>
```

## Fitur Playlist & Loop (baru)
- Add Video(s): pilih beberapa file sekaligus (multi-select)
- Tampilkan playlist di GUI dan atur urutan (Move Up/Down, Remove Selected)
- Loop Playlist: bila aktif, setelah file terakhir selesai akan kembali ke file pertama
- Status menampilkan file yang sedang di-stream: "Streaming: <current file>"

Catatan: setiap file dijalankan real-time (`-re`). Bila Loop aktif, runner akan mengulang playlist secara otomatis.

## Struktur Project
```
rtmp-client-live-stream/
  requirements.txt
  pyinstaller-mac.spec
  pyinstaller-win.spec
  rtmp_client/
    __init__.py
    __main__.py
    app.py
    core/
      __init__.py
      ffmpeg_runner.py
      validators.py
      settings.py
    ui/
      __init__.py
      main_window.py
```

## Prasyarat
- Python 3.10+ disarankan
- FFmpeg terinstall dan tersedia di PATH (`ffmpeg -version` harus jalan)
- pip terbaru: `python -m pip install --upgrade pip`

## Setup Environment
```
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows PowerShell

pip install -r requirements.txt
```

## Menjalankan Aplikasi (Dev)
```
python -m rtmp_client
```

## Build dengan PyInstaller
Pastikan FFmpeg ada di PATH di mesin build. Output ada di folder `dist/`.

### macOS (.app)
```
pyinstaller pyinstaller-mac.spec
# Hasil: dist/RTMP Client.app
```
Jika Apple Silicon, Anda bisa build universal atau arsitektur spesifik sesuai environment Python Anda.

### Windows (.exe)
Jalankan di Windows environment:
```
pyinstaller pyinstaller-win.spec
# Hasil: dist/rtmp-client/
```

### Linux (tanpa .spec khusus)
Contoh sederhana:
```
pyinstaller -n rtmp-client -w -m rtmp_client
```

## Next Steps (sudah disiapkan stubs)
- Random shuffle playlist
- Simpan & load playlist (.json)
- Progress bar durasi video
- Preview kecil (QtMultimedia/ffplay)

Kontribusi dipersilakan. PR/issue sangat membantu. 
