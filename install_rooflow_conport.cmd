@echo off
setlocal

echo --- Starting RooFlow config setup (with ConPort strategy update) ---

:: --- Dependency Checks ---
echo Checking dependencies...
call :CheckGit
if errorlevel 1 goto DependencyError
call :CheckPython
if errorlevel 1 goto DependencyError
call :CheckPyYAML
if errorlevel 1 goto DependencyError
echo All dependencies found.
:: --- End Dependency Checks ---

set "TEMP_CLONE_DIR=%TEMP%\RooFlowClone_%RANDOM%"
echo Cloning target: %TEMP_CLONE_DIR%

echo Cloning RooFlow repository...
git clone --depth 1 https://github.com/GreatScottyMac/RooFlow "%TEMP_CLONE_DIR%"
if %errorlevel% neq 0 (
    echo Error: Failed to clone RooFlow repository. Check your internet connection and Git setup.
    exit /b 1
)

if not exist "%TEMP_CLONE_DIR%\config" (
    echo Error: RooFlow repository clone seems incomplete. Config directory not found in temp location.
    if exist "%TEMP_CLONE_DIR%" rmdir /s /q "%TEMP_CLONE_DIR%" >nul 2>nul
    exit /b 1
)

:: --- MODIFIED COPY SECTION START ---
echo Copying specific configuration items...
set "COPY_ERROR=0"

echo Copying .roo directory...
robocopy "%TEMP_CLONE_DIR%\config\.roo" "%CD%\.roo" /E /NFL /NDL /NJH /NJS /nc /ns /np
if %errorlevel% gtr 7 (
    echo   ERROR: Failed to copy .roo directory. Robocopy Errorlevel: %errorlevel%
    set "COPY_ERROR=1"
) else (
    echo   Copied .roo directory.
)

if %COPY_ERROR% equ 0 (
    echo Copying .roomodes...
    robocopy "%TEMP_CLONE_DIR%\config" "%CD%" .roomodes /NFL /NDL /NJH /NJS /nc /ns /np
    if %errorlevel% gtr 7 (
        echo   ERROR: Failed to copy .roomodes using robocopy. Errorlevel: %errorlevel%
        set "COPY_ERROR=1"
    ) else (
        echo   Copied .roomodes.
    )
)

if %COPY_ERROR% equ 0 (
    echo Copying generate_mcp_yaml.py...
    copy /Y "%TEMP_CLONE_DIR%\config\generate_mcp_yaml.py" "%CD%\"
    if errorlevel 1 (
        echo   ERROR: Failed to copy generate_mcp_yaml.py.
        set "COPY_ERROR=1"
    ) else (
        echo   Copied generate_mcp_yaml.py.
    )
)

if %COPY_ERROR% equ 0 (
    echo Copying roo_code_conport_strategy...
    copy /Y "%TEMP_CLONE_DIR%\config\roo_code_conport_strategy" "%CD%\"
    if errorlevel 1 (
        echo   ERROR: Failed to copy roo_code_conport_strategy.
        set "COPY_ERROR=1"
    ) else (
        echo   Copied roo_code_conport_strategy.
    )
)
if %COPY_ERROR% equ 0 (
    echo Copying config/update_roo_prompts.ps1...
    copy /Y "%TEMP_CLONE_DIR%\config\update_roo_prompts.ps1" "%CD%\update_roo_prompts_temp.ps1"
    if errorlevel 1 (
        echo   ERROR: Failed to copy config/update_roo_prompts.ps1.
        set "COPY_ERROR=1"
    ) else (
        echo   Copied config/update_roo_prompts.ps1 as update_roo_prompts_temp.ps1.
    )
)

if %COPY_ERROR% equ 1 (
    echo ERROR: One or more essential files/directories could not be copied. Aborting setup.
    if exist "%TEMP_CLONE_DIR%" rmdir /s /q "%TEMP_CLONE_DIR%" >nul 2>nul
    exit /b 1
)
:: --- MODIFIED COPY SECTION END ---

:: Check if the essential copied items exist
if not exist "%CD%\.roo" (
    echo Error: .roo directory not found after specific copy. Setup failed.
    if exist "%TEMP_CLONE_DIR%" rmdir /s /q "%TEMP_CLONE_DIR%" >nul 2>nul
    exit /b 1
)
if not exist "%CD%\generate_mcp_yaml.py" (
    echo Error: generate_mcp_yaml.py not found after specific copy. Setup failed.
    if exist "%TEMP_CLONE_DIR%" rmdir /s /q "%TEMP_CLONE_DIR%" >nul 2>nul
    exit /b 1
)
if not exist "%CD%\roo_code_conport_strategy" (
    echo Error: roo_code_conport_strategy not found after specific copy. Setup failed.
    if exist "%TEMP_CLONE_DIR%" rmdir /s /q "%TEMP_CLONE_DIR%" >nul 2>nul
    exit /b 1
)
if not exist "%CD%\update_roo_prompts_temp.ps1" (
    echo Error: update_roo_prompts_temp.ps1 not found after specific copy. Setup failed.
    if exist "%TEMP_CLONE_DIR%" rmdir /s /q "%TEMP_CLONE_DIR%" >nul 2>nul
    exit /b 1
)

echo Running Python script to process templates...
for /f "tokens=*" %%a in ('powershell -NoProfile -Command "(Get-CimInstance Win32_OperatingSystem).Caption"') do set "OS_VAL=%%a"
set "SHELL_VAL=cmd"
set "HOME_VAL=%USERPROFILE%"
set "WORKSPACE_VAL=%CD%"

python generate_mcp_yaml.py --os "%OS_VAL%" --shell "%SHELL_VAL%" --home "%HOME_VAL%" --workspace "%WORKSPACE_VAL%"
if %errorlevel% neq 0 (
    echo Error: Python script generate_mcp_yaml.py failed to execute properly.
    if exist "%TEMP_CLONE_DIR%" rmdir /s /q "%TEMP_CLONE_DIR%" >nul 2>nul
    exit /b 1
)

:: --- EMBEDDED PROMPT UPDATE LOGIC (via PowerShell inline) ---
echo --- Starting Roo prompt update with ConPort strategy (using PowerShell) ---
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "update_roo_prompts_temp.ps1"
if %errorlevel% neq 0 (
    echo Error: PowerShell script update_roo_prompts_temp.ps1 for prompt updates failed.
    if exist "%CD%\update_roo_prompts_temp.ps1" del "%CD%\update_roo_prompts_temp.ps1" >nul 2>nul
    if exist "%TEMP_CLONE_DIR%" rmdir /s /q "%TEMP_CLONE_DIR%" >nul 2>nul
    exit /b 1
)
echo --- Roo prompt update with ConPort strategy completed (PowerShell) ---
:: --- END PROMPT UPDATE LOGIC ---

:: Clean up the strategy file from the workspace root
if exist "%CD%\roo_code_conport_strategy" (
    echo Cleaning up roo_code_conport_strategy from workspace root...
    del /F /Q "%CD%\roo_code_conport_strategy" >nul 2>nul
)
if exist "%CD%\update_roo_prompts_temp.ps1" (
    echo Cleaning up update_roo_prompts_temp.ps1 from workspace root...
    del /F /Q "%CD%\update_roo_prompts_temp.ps1" >nul 2>nul
)
:: --- MODIFIED CLEANUP SECTION START ---
echo Cleaning up temporary clone directory...
if exist "%TEMP_CLONE_DIR%" (
    rmdir /s /q "%TEMP_CLONE_DIR%" >nul 2>nul
    if errorlevel 1 (
       echo   Warning: Failed to completely remove temporary clone directory: %TEMP_CLONE_DIR%
    ) else (
       echo   Removed temporary clone directory.
    )
) else ( echo Temp clone directory not found to remove. )
:: --- MODIFIED CLEANUP SECTION END ---

echo --- RooFlow config setup (with ConPort strategy update) complete ---
goto ScriptEnd

:DependencyError
echo A required dependency (Git, Python, or PyYAML) was not found or failed check. Aborting.
if exist "%TEMP_CLONE_DIR%" rmdir /s /q "%TEMP_CLONE_DIR%" >nul 2>nul
exit /b 1

:ScriptEnd
goto :EOF

:: --- Subroutines ---
:CheckGit
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: git is not found in your PATH.
    echo Please install Git and ensure it's added to your system's PATH.
    echo You can download Git from: https://git-scm.com/download/win
    exit /b 1
)
echo   - Git found.
goto :EOF

:CheckPython
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: python is not found in your PATH.
    echo Please install Python 3 ^(https://www.python.org/downloads/^) and ensure it's added to PATH.
    exit /b 1
)
echo   - Python found.
goto :EOF

:CheckPyYAML
python -c "import yaml" >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: PyYAML library is not found for Python.
    echo Please install it using: pip install pyyaml
    exit /b 1
)
echo   - PyYAML library found.
goto :EOF
:: --- End Subroutines ---

endlocal
exit /b 0