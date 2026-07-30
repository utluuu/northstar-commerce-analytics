#Requires -Version 5.1
<#
.SYNOPSIS
    Northstar Commerce Analytics Power BI modelini otomatik oluşturur.

.DESCRIPTION
    1. Python ile model.bim dosyasını üretir (22 tablo, 24 ilişki, 87 ölçü)
    2. İsteğe bağlı olarak pbi-tools ile PBIT derlemeyi dener

.EXAMPLE
    .\scripts\Build-NorthstarPowerBI.ps1
#>
[CmdletBinding()]
param(
    [string]$CsvRoot = "",
    [switch]$SkipPbit
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$GeneratedDir = Join-Path $ProjectRoot "powerbi\automation\generated"
$DefaultCsvRoot = Join-Path $ProjectRoot "data\processed"

if ([string]::IsNullOrWhiteSpace($CsvRoot)) {
    $CsvRoot = $DefaultCsvRoot
}

Write-Host "Northstar Power BI modeli olusturuluyor..." -ForegroundColor Cyan
Write-Host "CSV klasoru: $CsvRoot"

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$Generator = Join-Path $ProjectRoot "scripts\generate_powerbi_model.py"
& $Python $Generator $CsvRoot
if ($LASTEXITCODE -ne 0) {
    throw "Model olusturma basarisiz."
}

Write-Host ""
Write-Host "Model basariyla olusturuldu:" -ForegroundColor Green
Write-Host "  $(Join-Path $GeneratedDir 'model.bim')"
Write-Host ""
Write-Host "Sonraki adimlar:" -ForegroundColor Yellow
Write-Host "  1. Tabular Editor indirin: https://tabulareditor.com/"
Write-Host "  2. Power BI Desktop acin (bos rapor)"
Write-Host "  3. Tabular Editor -> File -> Open -> From File -> model.bim"
Write-Host "  4. Model -> Deploy -> Power BI Desktop"
Write-Host "  5. Power BI'da veriyi yenileyin"
Write-Host ""
Write-Host "Detayli rehber: powerbi\automation\generated\KURULUM_TR.md"

if ($SkipPbit) {
    return
}

$PbiTools = Get-Command pbi-tools -ErrorAction SilentlyContinue
if (-not $PbiTools) {
    Write-Host ""
    Write-Host "pbi-tools bulunamadi. PBIT derlemesi atlaniyor." -ForegroundColor DarkYellow
    Write-Host "Kurulum: dotnet tool install --global pbi-tools"
    return
}

Write-Host ""
Write-Host "PBIT derlemesi deneniyor..." -ForegroundColor Cyan
$PbixProjDir = Join-Path $GeneratedDir "Northstar.pbip"
if (-not (Test-Path $PbixProjDir)) {
    Write-Host "PbixProj klasoru henuz yok; Tabular Editor yontemini kullanin." -ForegroundColor DarkYellow
    return
}

$pbitPath = Join-Path $GeneratedDir "Northstar Commerce Analytics.pbit"
Push-Location $GeneratedDir
try {
    pbi-tools compile $PbixProjDir -format PBIT -outPath $pbitPath
    if ($LASTEXITCODE -eq 0) {
        Write-Host "PBIT olusturuldu: $pbitPath" -ForegroundColor Green
    }
}
finally {
    Pop-Location
}
