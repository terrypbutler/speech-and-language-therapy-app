$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $projectPython)) {
    throw "The project environment is missing. Follow the setup steps in README.md first."
}

& $projectPython -m streamlit run (Join-Path $projectRoot "app.py")
