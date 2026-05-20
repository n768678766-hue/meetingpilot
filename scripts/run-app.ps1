Set-Location -LiteralPath $PSScriptRoot\..

$venvPython = Join-Path (Get-Location) ".venv\Scripts\python.exe"
if (Test-Path -LiteralPath $venvPython) {
    & $venvPython -m streamlit run src\meetingpilot\app.py
}
else {
    python -m streamlit run src\meetingpilot\app.py
}
