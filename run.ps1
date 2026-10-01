param(
    [Parameter(Position=0)]
    [string]$Action = "help",
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$RemainingArgs
)

$PythonExe = if (Test-Path "venv\Scripts\python.exe") { "venv\Scripts\python.exe" } else { "python" }

& $PythonExe run.py $Action $RemainingArgs
