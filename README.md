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

## Fitur Playlist & Loop
- Add Video(s): pilih beberapa file sekaligus (multi-select)
- Tampilkan playlist di GUI dan atur urutan (Move Up/Down, Remove Selected)
- Loop Playlist: bila aktif, setelah file terakhir selesai akan kembali ke file pertama
- Status menampilkan file yang sedang di-stream: "Streaming: <current file>"

## Preview & Kualitas Koneksi
- Preview video lokal yang sedang di-stream (QtMultimedia), tanpa suara
- Parsing log FFmpeg untuk menampilkan FPS, bitrate (kbps), dan speed

## Bundling FFmpeg (tanpa install terpisah)
Aplikasi akan mencoba memakai FFmpeg dari folder vendor yang dibundel. Jika tidak ada, fallback ke `PATH`.

Struktur vendor:
```
rtmp_client/vendor/
  darwin/ffmpeg
  windows/ffmpeg.exe + ffprobe.exe + *.dll
  linux/ffmpeg
```

- Windows disarankan menyalin seluruh isi folder `bin` dari distribusi FFmpeg (EXE + DLL) ke `rtmp_client/vendor/windows/` agar tidak ada dependency yang hilang.
- macOS/Linux cukup `ffmpeg` executable.

Salin otomatis dari PATH:
```
python scripts/copy_ffmpeg_to_vendor.py
```
Atau berikan sumber secara eksplisit (contoh Windows, arahkan ke ffmpeg.exe atau folder bin):
```
python scripts/copy_ffmpeg_to_vendor.py "C:\\ffmpeg\\bin"
```

Build dengan PyInstaller akan menyertakan folder vendor jika ada.

## Struktur Project
```
rtmp-client-live-stream/
  requirements.txt
  pyinstaller-mac.spec
  pyinstaller-win.spec
  scripts/
    copy_ffmpeg_to_vendor.py
  rtmp_client/
    __init__.py
    __main__.py
    app.py
    core/
      __init__.py
      ffmpeg_runner.py
      validators.py
      settings.py
      ffmpeg_resolver.py
    ui/
      __init__.py
      main_window.py
    vendor/
      .keep
```

## Prasyarat
- Python 3.10+ disarankan
- (opsional) FFmpeg di PATH jika tidak bundling vendor
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
Pastikan folder `rtmp_client/vendor/` berisi ffmpeg untuk platform target bila ingin bundling.

### macOS (.app)
```
python scripts/copy_ffmpeg_to_vendor.py   # opsional, untuk bundling
pyinstaller pyinstaller-mac.spec
# Hasil: dist/RTMP Client.app
```

### Windows (.exe)
Jalankan di Windows environment:
```
python scripts/copy_ffmpeg_to_vendor.py   # opsional, untuk bundling
pyinstaller pyinstaller-win.spec
# Hasil: dist/rtmp-client/
```

### Linux (tanpa .spec khusus)
Contoh sederhana:
```
pyinstaller -n rtmp-client -w -m rtmp_client --add-data "rtmp_client/vendor:rtmp_client/vendor"
```

## Next Steps (stubs tersedia)
- Random shuffle playlist
- Simpan & load playlist (.json)
- Progress bar durasi video
- Preview kecil (QtMultimedia/ffplay) – sudah ada preview basic

Kontribusi dipersilakan. PR/issue sangat membantu. 
