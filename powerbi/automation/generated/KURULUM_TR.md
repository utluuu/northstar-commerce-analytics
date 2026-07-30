# Northstar Power BI Otomatik Kurulum

Bu klasör, Power BI modelini sizin yerinize otomatik oluşturur.

## Oluşturulan dosyalar

- `model.bim` — 22 tablo, 24 ilişki, 87 DAX ölçüsü
- `CsvRoot.txt` — CSV klasör yolu

## Yöntem A — Tabular Editor (önerilen)

1. [Tabular Editor](https://tabulareditor.com/) indirin (ücretsiz sürüm yeterli).
2. Power BI Desktop'u açın → boş rapor oluşturun.
3. Tabular Editor'de **File → Open → From DB** → çalışan Power BI Desktop örneğine bağlanın.
4. **File → Open → From File** ile `model.bim` dosyasını açın (mevcut modelin üzerine yazar).
5. **Model → Deploy** ile Power BI Desktop'a aktarın.
6. Power BI'da **Transform data** → `CsvRoot` parametresinin değerini kontrol edin:
   `C:\Users\utluu\OneDrive\Masaüstü\northstar-commerce-analytics\northstar-commerce-analytics-v1.0.0\northstar-commerce-analytics\data\processed`
7. **Close & Apply** → veri yenilensin.
8. **View → Themes → Browse for themes** → `../theme.json`
9. İlk sayfayı oluşturmaya başlayın (Executive Overview).

## Yöntem B — pbi-tools ile PBIT

PowerShell'de proje kökünden:

```powershell
.\scripts\Build-NorthstarPowerBI.ps1
```

Bu komut `Northstar Commerce Analytics.pbit` dosyası üretmeye çalışır.
PBIT dosyasını Power BI Desktop ile açın, `CsvRoot` yolunu onaylayın ve yenileyin.

## Not

Görsel/dashboard tasarımı (6 sayfa) Power BI Desktop'ta elle yapılmalıdır.
Model katmanı (veri + ilişki + ölçüler) bu otomasyonla hazır gelir.

Detaylı sayfa tasarımı için: `../BUILD_POWERBI.md`
