@echo off
:: compile.bat — Build the Logos benchmark using MSVC (auto-configures environment)
:: Run from any Command Prompt window (does not need to be a Developer Prompt).
::
:: Usage: compile.bat
::        compile.bat run      (build + run)

setlocal

:: Locate vcvarsall.bat — set up MSVC environment
set VCVARS="C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvarsall.bat"
if not exist %VCVARS% (
    set VCVARS="C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat"
)
if not exist %VCVARS% (
    echo ERROR: Could not find vcvarsall.bat. Is Visual Studio 2022 installed?
    exit /b 1
)

:: Initialize the x64 native tools environment
call %VCVARS% x64 >nul 2>&1

:: Change to this script's directory
cd /d "%~dp0"

:: Build
echo Building LogosSort Logos/C benchmark...
cl /O2 /std:c11 /W0 ^
   logos_sort.c timsort.c bench.c ^
   /link /out:bench.exe

if errorlevel 1 (
    echo BUILD FAILED.
    exit /b 1
)
echo Build succeeded: bench.exe

if "%1"=="run" (
    echo.
    bench.exe
)
endlocal
