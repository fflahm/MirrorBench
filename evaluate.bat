@echo off
setlocal enabledelayedexpansion

set "bodies=male_0 male_1 female_0 female_1"
set "hands=mano_white mano_brown mano_purple"
set "marks=splash leaf_0 leaf_1 bread"

if "%~1"=="" (
    echo Usage: evaluate.bat MODEL_NAME
    exit /b 1
)
set "model=%~1"

echo Using model: %model%
echo.

for %%l in (0 1 2 3) do (
    for %%b in (%bodies%) do (
        for %%h in (%hands%) do (
            for %%m in (%marks%) do (
                %ISAACSIM_ROOT%\python.bat inference.py --body %%b --hand %%h --mark %%m --level %%l --model %model% --headless
                )
            )
        )
    )

set "bodies=tienkung GR1_T2 nova_carter"
set "hands=allegro shadow_hand Robotiq_2F_85"
set "marks=logo_0 logo_1"

for %%l in (0 1 2 3) do (
    for %%b in (%bodies%) do (
        for %%h in (%hands%) do (
            for %%m in (%marks%) do (
                %ISAACSIM_ROOT%\python.bat inference.py --body %%b --hand %%h --mark %%m --level %%l --model %model% --headless
                )
            )
        )
    )

endlocal