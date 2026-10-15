# «باحث» — مثبّت ويندوز بسطر واحد: يثبّت Python إن لزم، وينزّل البرنامج أو يحدّثه دون مساس بمشاريعكم وذاكرتكم،
# ويثبّت الحزمة، ويستعيد الذاكرة الخاصة إن وُجدت نسختها الاحتياطية، وينشئ الأيقونة، ويفتح اللوحة ويتحقق أنها قامت.
# التشغيل من الإنترنت (الصقوا السطر في PowerShell العادي، دون صلاحيات المسؤول):
#   $f="$env:TEMP\bahith-install.ps1"; iwr https://raw.githubusercontent.com/7r425ypz9t-hue/researchdepart/refs/heads/claude/clever-carson-78yimu/launchers/install_windows.ps1 -OutFile $f; powershell -NoProfile -ExecutionPolicy Bypass -File $f
# ملف نصي مقروء: لا ترميز ولا ملفات تنفيذية؛ وسياسة التنفيذ تُتجاوز لهذه العملية وحدها لا للجهاز.
param(
    [string]$Source = "",                               # نسخة محلية من المستودع بدل التنزيل
    [string]$Root = "",                                 # مجلد التثبيت (افتراضياً: التثبيت القائم، وإلا «المستندات\Bahith»)
    [string]$Ref = "claude/clever-carson-78yimu",       # الفرع المنزَّل؛ وإن تعذّر فـ main
    [switch]$NoLaunch                                   # للاختبار: بلا pip ولا أيقونة ولا تشغيل
)
$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"; $env:PYTHONIOENCODING = "utf-8"
$ProgressPreference = "SilentlyContinue"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }
$Repo  = "https://github.com/7r425ypz9t-hue/researchdepart"
$Home_ = if ($env:USERPROFILE) { $env:USERPROFILE } else { $HOME }
$Rk    = Join-Path $Home_ ".rkpos"

function Say($m) { Write-Host ("  » " + $m) -ForegroundColor Cyan }
function Fail($m) {
    Write-Host ("  ✖ " + $m) -ForegroundColor Red
    if (-not $NoLaunch) { Read-Host "اضغط Enter للإغلاق" | Out-Null }
    exit 1
}

# في Windows PowerShell 5.1 يتحول أي تحذير يكتبه برنامج خارجي إلى خطأ قاتل تحت Stop؛ فتُشغَّل البرامج الخارجية بهذا الغلاف
function Run-Native([scriptblock]$Block) {
    $old = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try { & $Block } finally { $ErrorActionPreference = $old }
}

function Is-Bahith($dir) { return $dir -and (Test-Path (Join-Path $dir "runtime\rkpos\__main__.py")) }

function Stop-Bahith {
    # إيقاف لوحة قائمة: لا يُنقل في ويندوز مجلد يعمل منه برنامج
    if (-not (Get-Command Get-CimInstance -ErrorAction SilentlyContinue)) { return }
    Get-CimInstance Win32_Process -Filter "Name like 'python%'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -like "*-m rkpos*" } |
        ForEach-Object { Invoke-CimMethod -InputObject $_ -MethodName Terminate -ErrorAction SilentlyContinue | Out-Null }
    Start-Sleep -Milliseconds 800
}

function Find-Root {
    # التثبيت القائم أولاً، كي تبقى المشاريع في مكانها: السجل، ثم آخر تشغيل للوحة، ثم اختصار سطح المكتب
    foreach ($f in @("install.json", "panel.json")) {
        try { $r = (Get-Content (Join-Path $Rk $f) -Raw -Encoding UTF8 | ConvertFrom-Json).root; if (Is-Bahith $r) { return $r } } catch { }
    }
    try {
        $desk = [Environment]::GetFolderPath("Desktop")
        $lnk = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $desk "باحث.lnk"))
        if (Is-Bahith $lnk.WorkingDirectory) { return $lnk.WorkingDirectory }
    } catch { }
    $docs = [Environment]::GetFolderPath("MyDocuments")
    if (-not $docs) { $docs = $Home_ }
    foreach ($d in @("researchdepart-main", "researchdepart")) { if (Is-Bahith (Join-Path $docs $d)) { return (Join-Path $docs $d) } }
    return (Join-Path $docs "Bahith")
}

function Find-Python {
    $cands = @(
        @{ exe = "py"; args = @("-3") },
        @{ exe = "python"; args = @() },
        @{ exe = "python3"; args = @() }
    )
    if ($env:LOCALAPPDATA) {
        foreach ($v in @("313", "312", "311", "310")) { $cands += @{ exe = (Join-Path $env:LOCALAPPDATA "Programs\Python\Python$v\python.exe"); args = @() } }
    }
    foreach ($c in $cands) {
        try {
            $exe = $c.exe; $a = @($c.args + @("-c", "import sys;print(sys.executable if sys.version_info>=(3,10) else '')"))
            $out = Run-Native { & $exe @a 2>$null }
            if ($LASTEXITCODE -eq 0 -and $out -and (Test-Path $out.Trim())) { return $out.Trim() }
        } catch { }
    }
    return $null
}

function Copy-UserData($old, $new) {
    # ينقل ما في قائمة user-data.txt (من الإصدار الجديد) من التثبيت السابق، فيغلب ما للمؤلف ما في الإصدار
    $list = Join-Path $new "launchers\user-data.txt"
    if (-not (Test-Path $list)) { Fail "قائمة بيانات المؤلف مفقودة من الإصدار الجديد؛ أُوقف التحديث حفاظاً على بياناتكم." }
    $n = 0
    foreach ($line in Get-Content $list -Encoding UTF8) {
        $p = $line.Trim()
        if (-not $p -or $p.StartsWith("#")) { continue }
        $items = @(Get-Item -Path (Join-Path $old ($p -replace "/", [IO.Path]::DirectorySeparatorChar)) -Force -ErrorAction SilentlyContinue)
        foreach ($it in $items) {
            $rel = $it.FullName.Substring($old.TrimEnd("\", "/").Length).TrimStart("\", "/")
            $dest = Join-Path $new $rel
            New-Item -ItemType Directory -Force -Path (Split-Path $dest) | Out-Null
            if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
            Copy-Item -Recurse -Force -Path $it.FullName -Destination $dest
            $n++
        }
    }
    return $n
}

Write-Host ""
Write-Host "  باحث — مؤسسة البحث والتطوير المعرفي" -ForegroundColor Yellow
Write-Host "  التثبيت والتحديث على هذا الجهاز" -ForegroundColor Yellow
Write-Host ""

# 1) Python 3.10 أو أحدث
Say "التحقق من Python…"
$py = Find-Python
if (-not $py) {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Say "تثبيت Python 3.12 (مرة واحدة، دقيقة أو دقيقتان)…"
        Run-Native { winget install -e --id Python.Python.3.12 --scope user --silent --accept-package-agreements --accept-source-agreements | Out-Null }
        $py = Find-Python
    }
    if (-not $py) {
        Start-Process "https://www.python.org/downloads/windows/"
        Fail "لم يُعثر على Python. ثبّتوه من الصفحة التي فُتحت (مع خيار Add python.exe to PATH)، ثم أعيدوا تشغيل هذا المثبّت."
    }
}
$pyw = Join-Path (Split-Path $py) "pythonw.exe"
if (-not (Test-Path $pyw)) { $pyw = $py }
Say ("Python: " + $py)

# 2) ملفات البرنامج
if (-not $Root) { $Root = Find-Root }
$Root = [IO.Path]::GetFullPath($Root)
$parent = Split-Path $Root
New-Item -ItemType Directory -Force -Path $parent | Out-Null
Say ("مجلد البرنامج: " + $Root)

if (Test-Path (Join-Path $Root ".git")) {
    # نسخة git: تُحدَّث بأداتها لا بالاستبدال، فلا يضيع تاريخها ولا فرعها
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { Fail "المجلد نسخة git ولا يوجد git على الجهاز. حدّثوه بأنفسكم ثم أعيدوا التشغيل." }
    Say "تحديث نسخة git…"
    Stop-Bahith
    Run-Native { git -C $Root pull --ff-only }
    if ($LASTEXITCODE -ne 0) { Fail "تعذّر تحديث نسخة git (تعديلات محلية أو فرع متباعد). لم يُمسّ شيء." }
} else {
    $staging = Join-Path $parent ("bahith-staging-" + [guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Force -Path $staging | Out-Null
    if ($Source) {
        Say "نسخ البرنامج من المجلد المحلي…"
        $new = Join-Path $staging "app"
        New-Item -ItemType Directory -Force -Path $new | Out-Null
        Get-ChildItem -Force $Source | Where-Object { $_.Name -ne ".git" } | Copy-Item -Recurse -Force -Destination $new
    } else {
        Say "تنزيل البرنامج…"
        $zipFile = Join-Path $staging "bahith.zip"
        $ok = $false
        foreach ($r in @($Ref, "main") | Select-Object -Unique) {
            try { Invoke-WebRequest -Uri "$Repo/archive/refs/heads/$r.zip" -OutFile $zipFile -UseBasicParsing; $ok = $true; break } catch { }
        }
        if (-not $ok) { Remove-Item -Recurse -Force $staging; Fail "تعذّر التنزيل. تحققوا من الاتصال ثم أعيدوا التشغيل." }
        Expand-Archive -Path $zipFile -DestinationPath $staging -Force
        Remove-Item $zipFile -Force
        $new = (Get-ChildItem $staging -Directory | Select-Object -First 1).FullName
    }
    if (-not (Is-Bahith $new)) { Remove-Item -Recurse -Force $staging; Fail "ملفات البرنامج ناقصة." }

    if (Is-Bahith $Root) {
        Say "نقل مشاريعكم وذاكرتكم وسجلاتكم إلى الإصدار الجديد…"
        Stop-Bahith
        $n = Copy-UserData $Root $new
        Say ("نُقل " + $n + " عنصراً من بيانات المؤلف.")
        # تُحفظ النسخة السابقة كاملة بجانب الجديدة حتى التثبيت التالي، احتياطاً
        $prev = $Root + ".previous"
        if (Test-Path $prev) { Remove-Item -Recurse -Force $prev }
        Move-Item $Root $prev
    } elseif (Test-Path $Root) {
        Remove-Item -Recurse -Force $staging
        Fail ("المجلد " + $Root + " موجود وليس فيه «باحث». اختاروا مجلداً آخر: -Root ""مسار""")
    }
    Move-Item $new $Root
    Remove-Item -Recurse -Force $staging -ErrorAction SilentlyContinue
}

New-Item -ItemType Directory -Force -Path $Rk | Out-Null
@{ root = $Root; ref = $Ref; installed_at = (Get-Date).ToString("s") } | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $Rk "install.json")
if ($NoLaunch) { Say "تم (وضع الاختبار)."; exit 0 }

Push-Location $Root
try {
    # 3) الحزمة ومتطلباتها (PyYAML وjsonschema وpython-docx) مثبتة على المجلد نفسه، ومعها Pillow لصور الأيقونة
    Say "تثبيت الحزمة ومتطلباتها…"
    Run-Native { & $py -m pip install --quiet --disable-pip-version-check -e . pillow 2>&1 | Out-Null }
    if ($LASTEXITCODE -ne 0) {
        Run-Native { & $py -m pip install --user --quiet --disable-pip-version-check -e . pillow }
        if ($LASTEXITCODE -ne 0) { Fail "تعذّر تثبيت الحزمة (pip). أرسلوا لقطة من هذه النافذة." }
    }

    # 4) الذاكرة الخاصة من نسختها الاحتياطية إن لم تكن موجودة
    $priv = Join-Path $Root "memory\author\private"
    if (-not (Test-Path $priv)) {
        $downloads = Join-Path $Home_ "Downloads"
        foreach ($b in @((Join-Path $Root "midad-private-backup.tar.gz"), (Join-Path $downloads "midad-private-backup.tar.gz"))) {
            if (Test-Path $b) { Say "استعادة الذاكرة الخاصة…"; Run-Native { tar -xzf $b -C $Root }; break }
        }
    }

    # 5) الأيقونة، وخط الهوية في النظام إن كان مودعاً
    Say "إنشاء الأيقونة على سطح المكتب وفي قائمة البرامج…"
    Run-Native { & $py -m rkpos install-icon | Out-Null }
    if ($LASTEXITCODE -ne 0) { Fail "تعذّر إنشاء الأيقونة." }
    if (Test-Path (Join-Path $Rk "fonts\adwa-assalaf.ttf")) { Run-Native { & $py -m rkpos fonts system 2>$null | Out-Null } }

    # 6) التشغيل والتحقق من أن اللوحة قامت فعلاً
    Say "فتح لوحة التحكم…"
    $state = Join-Path $Rk "panel.json"
    Stop-Bahith
    Remove-Item $state -ErrorAction SilentlyContinue
    Start-Process -FilePath $pyw -ArgumentList "-m", "rkpos", "panel" -WorkingDirectory $Root
    $up = $false
    for ($i = 0; $i -lt 40; $i++) {
        Start-Sleep -Milliseconds 500
        try {
            $port = (Get-Content $state -Raw -Encoding UTF8 | ConvertFrom-Json).port
            Invoke-WebRequest -Uri "http://127.0.0.1:$port/" -UseBasicParsing -TimeoutSec 2 | Out-Null; $up = $true; break
        } catch { }
    }
    if (-not $up) {
        Write-Host ""
        Write-Host "  ✖ لم تبدأ اللوحة. هذا ما أعاده التشغيل — أرسلوه كما هو:" -ForegroundColor Red
        Run-Native { & $py -c "import rkpos.panel.server; print('rkpos.panel: OK')" 2>&1 | Select-Object -First 30 }
        $log = Join-Path $Rk "panel.log"
        if (Test-Path $log) { Get-Content $log -Tail 20 -Encoding UTF8 }
        if (-not $NoLaunch) { Read-Host "اضغط Enter للإغلاق" | Out-Null }
        exit 1
    }
} finally { Pop-Location }

Write-Host ""
Write-Host "  ✔ اكتمل التثبيت، واللوحة تعمل. من الآن: انقروا أيقونة «باحث» على سطح المكتب." -ForegroundColor Green
Write-Host ("  البرنامج ومشاريعكم: " + $Root) -ForegroundColor Gray
if (Test-Path ($Root + ".previous")) { Write-Host ("  النسخة السابقة محفوظة احتياطاً في: " + $Root + ".previous") -ForegroundColor Gray }
Write-Host ""
