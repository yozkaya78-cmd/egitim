---
name: video-indir
description: Video analizi istendiginde verilen linki (YouTube, TikTok, Instagram, X, Vimeo vb.) yt-dlp ile ~/Downloads/video-analiz/ altinda tarihli bir klasore indirir; konusma onemliyse sesi ayrica WAV olarak ceker. "Su videoyu analiz et", "bu linki indir", "videoyu incele" gibi isteklerde kullan. Kare analizi icin ardindan /kare-cikar skill'ini calistir.
---

# video-indir

Bir video linkini analiz icin yerel diske indirir. Ciktilar her zaman
`~/Downloads/video-analiz/<TARIH>_<slug>/` klasorune gider; boylece ayni gun
birden fazla video analiz edilse bile karismaz.

## Ne zaman kullanilir

- Kullanici bir video linki verip analiz, ozet, inceleme, kare cikarma,
  kanca/CTA analizi veya transkript istediginde.
- `/kare-cikar` calistirilmadan once video diskte yoksa.

## On kosullar

Asagidaki komutla araclari kontrol et; eksik olan varsa kur:

```bash
which yt-dlp ffmpeg ffprobe || {
  pip3 install -q yt-dlp
  sudo apt-get install -y -q ffmpeg
}
```

## Adimlar

### 1. Klasoru olustur

Tarih `YYYY-MM-DD` formatinda, slug ise video basligindan (yoksa video
id'sinden) turetilir. Once basligi al:

```bash
URL="<kullanicinin verdigi link>"
TITLE=$(yt-dlp --get-title --no-playlist "$URL" 2>/dev/null | head -1)
ID=$(yt-dlp --get-id --no-playlist "$URL" 2>/dev/null | head -1)
SLUG=$(echo "${TITLE:-$ID}" | iconv -f utf8 -t ascii//TRANSLIT 2>/dev/null \
  | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]+/-/g; s/[^a-z0-9]/-/g; s/--*/-/g; s/^-//; s/-$//' | cut -c1-40)
DIR=~/Downloads/video-analiz/$(date +%Y-%m-%d)_${SLUG:-video}
mkdir -p "$DIR"
echo "$DIR"
```

Ayni isimde klasor zaten varsa uzerine yazma; sonuna `_2`, `_3` ekle.

### 2. Videoyu indir

Analiz icin 1080p yeterlidir; daha buyugu sadece disk ve sure yer.
Ses ve goruntu tek MP4 dosyasinda birlestirilir.

```bash
yt-dlp --no-playlist \
  -f "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080][ext=mp4]/b" \
  --merge-output-format mp4 \
  -o "$DIR/video.%(ext)s" \
  --write-info-json --write-thumbnail \
  --write-subs --write-auto-subs --sub-langs "tr,en" --sub-format "vtt/srt" \
  "$URL"
```

Notlar:
- `--write-info-json` baslik, sure, kanal, aciklama, goruntulenme gibi
  metadata'yi `video.info.json` olarak kaydeder; rapor yazarken kullan.
- Altyazi varsa `video.tr.vtt` / `video.en.vtt` gelir; konusma analizi icin
  once bunlara bak, WAV cikarmaya gerek kalmayabilir.
- Instagram / TikTok gibi platformlarda format secimi basarisiz olursa
  sadece `-f b` ile tekrar dene.
- Cerez gerektiren (giris istemli) icerikte kullaniciya
  `--cookies-from-browser chrome` secenegini soyle; kendin cerez dosyasi arama.

### 3. Konusma onemliyse sesi WAV olarak cikar

Konusma onemlidir eger: videoda anlatim / rop / roportaj varsa, kullanici
transkript veya "ne diyor" tarzi bir sey istiyorsa, ya da altyazi inmemisse.
Sadece muzik + gorsel olan videolarda bu adimi atla.

```bash
ffmpeg -y -loglevel error -i "$DIR/video.mp4" \
  -vn -ac 1 -ar 16000 -c:a pcm_s16le "$DIR/audio.wav"
```

16 kHz mono PCM, Whisper ve benzeri konusma tanima araclarinin bekledigi
formattir. Sonra sistemde `whisper` varsa transkript uret:

```bash
which whisper && whisper "$DIR/audio.wav" --language tr --model small \
  --output_dir "$DIR" --output_format txt
```

Whisper yoksa bunu raporda belirt; kurmayi teklif et ama zorla kurma.

### 4. Dogrula ve ozetle

```bash
ls -la "$DIR"
ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate \
  -of default=noprint_wrappers=1 "$DIR/video.mp4"
```

Kullaniciya kisa bir ozet ver:
- Klasor yolu
- Baslik, kanal, sure, cozunurluk (info.json'dan)
- Hangi dosyalar olustu (video.mp4, audio.wav, altyazi, transkript)
- Sonraki adim: kare analizi icin `/kare-cikar` calistir.

## Klasor yapisi

```
~/Downloads/video-analiz/2026-09-05_ornek-video/
├── video.mp4
├── video.info.json
├── video.webp            (kucuk resim)
├── video.tr.vtt          (varsa altyazi)
├── audio.wav             (konusma onemliyse)
├── audio.txt             (whisper varsa transkript)
└── frames/               (kare-cikar skill'i doldurur)
```

## Hata durumlari

| Belirti | Cozum |
|---|---|
| `Requested format is not available` | `-f b` ile tekrar dene |
| `Sign in to confirm you're not a bot` | Kullanicidan cerez iste (`--cookies-from-browser`) |
| `yt-dlp: command not found` | `pip3 install yt-dlp` |
| `ffmpeg not found` (merge asamasinda) | `sudo apt-get install ffmpeg` |
| Cok eski yt-dlp, site desteklenmiyor | `pip3 install -U yt-dlp` |
| `Output file does not contain any stream` (WAV adiminda) | Videoda ses yok; `ffprobe -show_streams` ile dogrula, WAV adimini atla ve raporda belirt |
