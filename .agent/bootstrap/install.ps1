# Agent Bridge bootstrap (Windows) — delegates to install.py
$ErrorActionPreference = "Stop"
$Py = Get-Command python -ErrorAction SilentlyContinue
if (-not $Py) { $Py = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $Py) { throw "Python not found" }
& $Py.Source (Join-Path $PSScriptRoot "install.py") @args
