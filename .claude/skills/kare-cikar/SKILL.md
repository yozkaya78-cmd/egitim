---
name: kare-cikar
description: Indirilmis bir videodan ffmpeg ile saniyede 1 kare PNG cikarir (frames/ klasoru), kareleri sirayla acip inceler (sahnede ne var, ekrandaki yazi, gecisler) ve tek bir analiz raporu uretir - kanca ani, sahne akisi, ekran metinleri, CTA ani. "Kareleri cikar", "videoyu sahne sahne incele", "kancasini/CTA'sini bul", "ekran yazilarini oku" gibi isteklerde kullan. Video diskte yoksa once /video-indir calistir.
---

# kare-cikar

Videoyu 1 fps'de PNG karelere boler, kareleri gorsel olarak inceler ve
icerik ureticisinin ise yarayacagi tek bir rapor cikarir.

## Girdi

`~/Downloads/video-analiz/<TARIH>_<slug>/video.mp4` (video-indir ciktisi).
Kullanici baska bir yol verdiyse onu kullan. Birden fazla klasor varsa ve
kullanici belirtmediyse en yenisini al:

```bash
DIR=$(ls -td ~/Downloads/video-analiz/*/ 2>/dev/null | head -1)
VIDEO="$DIR/video.mp4"
[ -f "$VIDEO" ] || { echo "video yok, once /video-indir calistir"; }
```

## Adimlar

### 1. Sure ve kare sayisini ogren

```bash
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$VIDEO")
echo "sure: ${DUR}s -> yaklasik $(printf '%.0f' "$DUR") kare"
```

Video 10 dakikadan (600 kare) uzunsa kullaniciya soyle ve ya
`fps=1/2` (2 saniyede 1 kare) kullan ya da belirli bir araligi
(`-ss BASLANGIC -to BITIS`) analiz et. 600 kareyi tek tek acmak pratik degil.

### 2. Kareleri cikar

```bash
mkdir -p "$DIR/frames"
ffmpeg -y -loglevel error -i "$VIDEO" \
  -vf "fps=1,scale='min(1280,iw)':-2" \
  -start_number 0 "$DIR/frames/frame_%04d.png"
ls "$DIR/frames" | wc -l
```

- `fps=1` -> saniyede 1 kare; `frame_0000.png` = 0. saniye,
  `frame_0037.png` = 37. saniye. Dosya adi dogrudan zaman damgasidir.
- `scale=min(1280,iw)` genisligi 1280'e sinirlar; ekran yazilari hala
  okunur, dosyalar kucuk kalir.

### 3. Gecisleri otomatik tespit et (opsiyonel ama faydali)

Sahne degisimlerini gozle bulmadan once ffmpeg'e sordur:

```bash
ffmpeg -loglevel info -i "$VIDEO" -vf "select='gt(scene,0.3)',showinfo" \
  -f null - 2>&1 | grep -o 'pts_time:[0-9.]*' | cut -d: -f2 > "$DIR/scene_cuts.txt"
cat "$DIR/scene_cuts.txt"
```

Bu liste "gecisler nerede" sorusunun ilk cevabidir; kare incelemesinde
bu saniyelere ozellikle dikkat et. Esik 0.3 cok az/cok fazla kesim
veriyorsa 0.2-0.5 arasinda ayarla.

### 4. Kareleri sirayla incele

Kareleri **Read araciyla** ac (gorsel olarak gorursun). Sirayla git,
atlama yapma. Her kare icin su uc soruyu cevapla ve calisma notuna yaz:

1. **Sahnede ne var?** Kisi/nesne/mekan, kamera acisi (yakin/genis),
   hareket, ifade, renk-isik havasi.
2. **Ekranda hangi yazi var?** Altyazi, baslik, overlay, watermark,
   grafik uzerindeki rakamlar. Metni **aynen** yaz, yorumlama.
3. **Onceki kareye gore ne degisti?** Ayni sahne mi devam ediyor, kesim mi,
   yeni bir yazi mi girdi, kamera acisi mi degisti?

Verimli okuma icin:
- Ilk 5 kareyi (0-4 sn) tek tek ve dikkatle oku; kanca burada.
- Son 5 kareyi tek tek oku; CTA burada.
- Ortada, `scene_cuts.txt`'deki her kesimin +0 ve +1 saniyesini mutlaka oku.
- Kesimler arasinda sahne degismiyorsa 3-5 kare atlayarak ilerleyebilirsin,
  ama ekran yazisi girip cikan yerleri kacirmamak icin en az her 3. kareyi ac.
- Kare sayisi 120'nin altindaysa hepsini ac.

Transkript (`audio.txt`) veya altyazi (`video.*.vtt`) varsa kare
zamanlamasiyla eslestir; "X saniyede sunu diyor, ekranda su yazi var"
bicimi cok daha guclu bir rapor verir.

### 5. Tek rapor yaz

Raporu `$DIR/rapor.md` olarak kaydet ve ayni icerigi kullaniciya goster.
Sablon:

```markdown
# Video Analizi: <baslik>

Kaynak: <URL> | Sure: <mm:ss> | Cozunurluk: <WxH> | Kare sayisi: <N>

## 1. Kanca ani (ilk 3 saniye)
- **0-1 sn:** <ne goruluyor, ne yaziyor, ne soyleniyor>
- **1-3 sn:** <...>
- **Kanca turu:** <soru / sok / vaat / merak boslugu / gorsel kontrast>
- **Degerlendirme:** <izleyici neden kaydirmadan durur; guclu/zayif yani>

## 2. Sahne akisi
| # | Zaman | Sahne | Aciklama | Gecis turu |
|---|-------|-------|----------|------------|
| 1 | 0:00-0:03 | <kisa ad> | <ne oluyor> | - |
| 2 | 0:03-0:11 | <...> | <...> | sert kesim / jump cut / zoom / gecis efekti |
...

Ritim notu: <ortalama sahne suresi, tempo nerede hizlaniyor/yavasliyor>

## 3. Ekran metinleri
| Zaman | Metin (aynen) | Tur | Konum |
|-------|---------------|-----|-------|
| 0:00 | "..." | baslik / altyazi / overlay / grafik | ust / orta / alt |
...

## 4. CTA ani
- **Zaman:** <mm:ss>
- **Ekranda:** <yazi / buton / ok isareti>
- **Soylenen:** <transkriptten, varsa>
- **CTA turu:** <takip et / yorum yaz / link / kaydet / baska videoya yonlendirme>
- **Degerlendirme:** <net mi, erken mi gec mi, tekrar var mi>

## 5. Genel gozlemler
- <format: dikey/yatay, konusan kafa / b-roll / ekran kaydi>
- <altyazi stili, renk paleti, marka ogeleri>
- <ureticinin kendi videosunda kullanabilecegi 3 somut cikarim>
```

Sabit kurallar:
- Zamanlari `mm:ss` yaz; kare dosya adi (`frame_0037`) = 0:37.
- Ekran metnini tirnak icinde ve **aynen** ver; okunamiyorsa `[okunamadi]` de.
- Gormedigin seyi uydurma; emin olmadigin yerde "muhtemelen" de.
- Kanca ve CTA bulunamadiysa "yok" de ve neden oyle dusundugunu yaz.

### 6. Temizlik

Kareleri silme; kullanici tekrar bakmak isteyebilir. Disk sorunuysa
`frames/` klasorunu silmeden once sor.

## Hata durumlari

| Belirti | Cozum |
|---|---|
| `frames/` bos | Video yolu yanlis veya video bozuk; `ffprobe "$VIDEO"` ile kontrol et |
| Kareler tamamen siyah | Video ilk saniyelerde fade-in yapiyor olabilir; `frame_0003`'ten devam et |
| Ekran yazisi bulanik | `scale` filtresini kaldirip tam cozunurlukte tekrar cikar |
| Cok fazla kare | `fps=1/2` veya `-ss/-to` ile aralik sec |
