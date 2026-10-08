@echo off
rem MIDAD one-file installer for Windows. Double-click it. Safe to run again (it updates).
powershell -NoProfile -ExecutionPolicy Bypass -Command "$f='%~f0'; $s=[IO.File]::ReadAllText($f,[Text.Encoding]::UTF8); $m='#PS'+'START'; iex $s.Substring($s.IndexOf($m)+$m.Length)"
echo.
pause
exit /b
#PSSTART
$ErrorActionPreference = 'Continue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Add-Type -AssemblyName System.Windows.Forms
function Say($t) { Write-Host "==> $t" -ForegroundColor Cyan }
function Box($t, $icon = 'Information') {
  $o = [System.Windows.Forms.MessageBoxOptions]::RtlReading -bor [System.Windows.Forms.MessageBoxOptions]::RightAlign
  [void][System.Windows.Forms.MessageBox]::Show($t, 'مداد', 'OK', $icon, 'Button1', $o)
}
function Refresh-Path { $env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User') }

$Repo = 'https://github.com/7r425ypz9t-hue/researchdepart/archive/refs/heads/main.zip'
$Dir  = Join-Path $env:USERPROFILE 'Midad'

try {
  # 1) Python 3.10+
  Say 'Checking Python...'
  function Find-Python {
    foreach ($cand in @('py -3', 'python', 'python3')) {
      $c = @($cand -split ' ')
      if (-not (Get-Command $c[0] -ErrorAction SilentlyContinue)) { continue }
      try {
        $v = & $c[0] @($c | Select-Object -Skip 1) -c "import sys;print('%d.%d'%sys.version_info[:2])" 2>$null
        if ($LASTEXITCODE -eq 0 -and "$v".Trim() -match '^3\.(\d+)$' -and [int]$Matches[1] -ge 10) { return ,$c }
      } catch {}
    }
    return $null
  }
  $Py = Find-Python
  if (-not $Py) {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
      Say 'Installing Python 3.12 (winget)...'
      winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
      Refresh-Path
      $Py = Find-Python
    }
    if (-not $Py) {
      Start-Process 'https://www.python.org/downloads/windows/'
      Box "لم يُعثر على Python 3.10 أو أحدث.`nفتحتُ صفحة التنزيل: ثبّتوه مع تفعيل خيار Add python.exe to PATH، ثم شغّلوا هذا الملف مرة أخرى." 'Warning'
      exit 1
    }
  }
  $PyExe = $Py[0]; $PyArgs = @($Py | Select-Object -Skip 1)
  Say ("Python: " + ($Py -join ' '))

  # 2) Download / update the repository (private files are kept)
  Say "Downloading MIDAD into $Dir ..."
  $tmp = Join-Path $env:TEMP ('midad-' + [guid]::NewGuid().ToString('N'))
  New-Item -ItemType Directory -Path $tmp -ErrorAction Stop | Out-Null
  Invoke-WebRequest -Uri $Repo -OutFile (Join-Path $tmp 'midad.zip') -UseBasicParsing -ErrorAction Stop
  Expand-Archive -Path (Join-Path $tmp 'midad.zip') -DestinationPath $tmp -Force -ErrorAction Stop
  $src = Get-ChildItem $tmp -Directory | Where-Object { $_.Name -like 'researchdepart-*' } | Select-Object -First 1
  if (-not $src) { throw 'download did not contain the repository' }
  New-Item -ItemType Directory -Path $Dir -Force -ErrorAction Stop | Out-Null
  robocopy $src.FullName $Dir /E /NFL /NDL /NJH /NJS /NP | Out-Null
  if ($LASTEXITCODE -ge 8) { throw "copy failed (robocopy $LASTEXITCODE)" }
  Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue

  # 3) Install the package
  Say 'Installing the package (pip)...'
  & $PyExe @PyArgs -m pip install --disable-pip-version-check -q -e $Dir
  if ($LASTEXITCODE -ne 0) { & $PyExe @PyArgs -m pip install --disable-pip-version-check -q --user -e $Dir }
  if ($LASTEXITCODE -ne 0) { throw 'pip install failed' }

  # 4) Restore the private memory backup if found
  $restored = $false
  $places = @((Split-Path $f), (Join-Path $env:USERPROFILE 'Downloads'), (Join-Path $env:USERPROFILE 'Desktop'), $Dir)
  $bk = foreach ($p in $places) { if (Test-Path $p) { Get-ChildItem $p -Filter 'midad-private-backup*.tar.gz' -ErrorAction SilentlyContinue } }
  $bk = $bk | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if ($bk) {
    Say ("Restoring private memory from " + $bk.FullName)
    tar -xzf $bk.FullName -C $Dir
    if ($LASTEXITCODE -eq 0) { $restored = $true }
  }

  # 5) Claude Code (optional, for automatic runs with your Claude account)
  Refresh-Path
  $hasClaude = [bool](Get-Command claude -ErrorAction SilentlyContinue)
  if (-not $hasClaude) {
    $o = [System.Windows.Forms.MessageBoxOptions]::RtlReading -bor [System.Windows.Forms.MessageBoxOptions]::RightAlign
    $ans = [System.Windows.Forms.MessageBox]::Show("هل تريدون تثبيت Claude Code لتشغيل الوكلاء آلياً بحسابكم في Claude؟`n(بدونه تعمل اللوحة بالوضع اليدوي: نسخ البرومبت إلى claude.ai)", 'مداد', 'YesNo', 'Question', 'Button1', $o)
    if ($ans -eq 'Yes') {
      Say 'Installing Claude Code (official installer)...'
      powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://claude.ai/install.ps1 | iex"
      Refresh-Path
      foreach ($c in @((Join-Path $env:USERPROFILE '.local\bin\claude.exe'))) { if (Test-Path $c) { $env:Path += ';' + (Split-Path $c) } }
      $hasClaude = [bool](Get-Command claude -ErrorAction SilentlyContinue)
    }
  }

  # 6) Desktop icon
  Say 'Creating the desktop icon...'
  Push-Location $Dir
  & $PyExe @PyArgs -m rkpos install-icon
  $iconOk = ($LASTEXITCODE -eq 0)
  Pop-Location
  if (-not $iconOk) { throw 'install-icon failed' }

  $msg = "تم التثبيت في:`n$Dir`n`nظهرت أيقونة «مداد» على سطح المكتب وفي قائمة ابدأ."
  if ($restored) { $msg += "`n`n✓ استُعيدت الذاكرة الخاصة (البصمة والمشروع الأول)." }
  else { $msg += "`n`n! لم يُعثر على midad-private-backup.tar.gz: ضعوه في مجلد التنزيلات وأعيدوا تشغيل هذا الملف." }
  if ($hasClaude) { $msg += "`n`n✓ Claude Code موجود. إن لم تسجّلوا الدخول بعد: افتحوا PowerShell واكتبوا claude مرة واحدة." }
  else { $msg += "`n`nاللوحة تعمل بالوضع اليدوي، ويمكن إضافة Claude Code لاحقاً بإعادة تشغيل هذا الملف." }
  Box $msg
  $lnk = Join-Path ([Environment]::GetFolderPath('Desktop')) 'مداد.lnk'
  if (Test-Path $lnk) { Start-Process $lnk }
}
catch {
  Write-Host $_ -ForegroundColor Red
  Box ("تعذّر التثبيت:`n" + $_.Exception.Message + "`n`nصوّروا نافذة الأوامر السوداء وأرسلوها.") 'Error'
  exit 1
}
