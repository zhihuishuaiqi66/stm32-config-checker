@echo off
setlocal
cd /d "%~dp0"

rem ==== STM32F407ZGT6 self-test: flash -> reset -> read report from RAM ====
rem Build first (see ../README.md), then run this script.
rem Board: LXB407ZG-P1 V2.0 core board, HSE = 8MHz (NOT the 25MHz CubeMX assumes)

set CLI=D:\Clion\STM32CubeCLT_1.18.0\STM32CubeProgrammer\bin\STM32_Programmer_CLI.exe
set HEX=build\f407_selftest.hex
set ADDR=0x2000007C
set SIZE=2400

echo ================================================
echo   STM32F407ZGT6 self-test
echo ================================================
echo.

if not exist "%CLI%" (
  echo [ERR] STM32_Programmer_CLI not found:
  echo       %CLI%
  echo       Edit the CLI= line at the top of this script.
  goto fail
)
if not exist "%HEX%" (
  echo [ERR] firmware not found: %HEX%
  echo       Build it first (see ../README.md section 4).
  goto fail
)

echo [1/4] Flashing...
"%CLI%" -c port=SWD freq=4000 -w "%HEX%" -v
if errorlevel 1 goto fail

echo.
echo [2/4] Resetting the target (this step is why "flash ok but nothing runs")...
"%CLI%" -c port=SWD freq=4000 >nul
echo       done

echo.
echo [3/4] Waiting 10s for the tests to finish (timer test alone takes 2s)...
timeout /t 10 /nobreak >nul

echo.
echo [4/4] Reading report from RAM...
"%CLI%" -c port=SWD freq=4000 mode=HOTPLUG -u %ADDR% %SIZE% "report_readback.bin" >nul
if errorlevel 1 goto fail

echo.
echo ================= RESULT =================
powershell -NoProfile -Command "$b=[IO.File]::ReadAllBytes('report_readback.bin'); $t=[Text.Encoding]::UTF8.GetString($b); $i=$t.IndexOf([char]0); if($i -gt 0){$t=$t.Substring(0,$i)}; $t | Tee-Object -FilePath 'report_readback.txt'; exit 0"
echo ==========================================
echo.
echo Saved to: report_readback.txt
goto end

:fail
echo.
echo [FAIL] Check:
echo   1) ST-Link plugged into the PC
echo   2) board powered via Type-C (PWR LED on)
echo   3) SWD header order is +5V / GND / DIO / CLK  (NOT the Blue Pill order!)
echo      ST-Link GND -> GND, SWDIO -> DIO, SWCLK -> CLK, do NOT connect 3.3V
echo.

:end
echo Press any key to close...
pause >nul
exit /b 0
