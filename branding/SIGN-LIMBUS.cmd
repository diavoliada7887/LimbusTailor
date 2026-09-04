@echo off
setlocal
cd /d "%~dp0"

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$cert = Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert ^| Where-Object { $_.Subject -like '*CN=Arkhivum Software*' } ^| Sort-Object NotAfter -Descending ^| Select-Object -First 1; if (-not $cert) { Write-Host 'Arkhivum Software code-signing certificate not found.' -ForegroundColor Red; exit 2 }; $sig = Set-AuthenticodeSignature -FilePath '.\LimbusTailor.exe' -Certificate $cert -HashAlgorithm SHA256; Write-Host ('Signature status: ' + $sig.Status); if ($sig.Status -ne 'Valid') { exit 3 }; Start-Process '.\LimbusTailor.exe'"

if errorlevel 1 (
  echo.
  echo Signing or launch failed. Press any key to close.
  pause >nul
)
