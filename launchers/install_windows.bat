@echo off
chcp 65001 >nul
rem ===== تثبيت لوحة «باحث» على ويندوز =====
rem المتطلبات: Python 3.10+ (python.org مع خيار Add to PATH) — واختيارياً Claude Code للتشغيل الآلي.
cd /d "%~dp0\.."
set PY=py -3
%PY% --version >nul 2>&1 || set PY=python
echo [1/3] تثبيت الحزمة...
%PY% -m pip install --upgrade pip >nul
%PY% -m pip install -e . || goto :fail
echo [2/3] استعادة الذاكرة الخاصة إن وُجدت النسخة الاحتياطية...
if exist "midad-private-backup.tar.gz" (
  tar -xzf "midad-private-backup.tar.gz" && echo     تمت الاستعادة.
) else if exist "%USERPROFILE%\Downloads\midad-private-backup.tar.gz" (
  tar -xzf "%USERPROFILE%\Downloads\midad-private-backup.tar.gz" && echo     تمت الاستعادة من مجلد التنزيلات.
) else (
  echo     لم تُعثر على midad-private-backup.tar.gz — تعمل اللوحة بلا بصمة الأسلوب حتى تُستعاد.
)
echo [3/3] إنشاء الأيقونة على سطح المكتب...
%PY% -m rkpos install-icon || goto :fail
echo.
echo تم. افتحوا أيقونة «باحث» من سطح المكتب.
pause
exit /b 0
:fail
echo تعذّر التثبيت. أرسلوا لقطة من هذه النافذة.
pause
exit /b 1
