# viktor-local for Windows: irm https://ocb2016.me/viktor-local/install.ps1 | iex
# Installs a `viktor-local` command; later just run: viktor-local C:\games
$url = if ($env:VIKTOR_LOCAL_URL) { $env:VIKTOR_LOCAL_URL } else { "https://ocb2016.me/viktor-local/viktor_local.py" }
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { irm https://astral.sh/uv/install.ps1 | iex; $env:Path = "$env:USERPROFILE\.local\bin;$env:Path" }
$dir = "$env:USERPROFILE\.cache\viktor-local"; $bin = "$env:USERPROFILE\.local\bin"
New-Item -ItemType Directory -Force $dir, $bin | Out-Null
irm $url -OutFile "$dir\viktor_local.py"
Set-Content "$bin\viktor-local.cmd" "@echo off`r`nif `"%~1`"==`"update`" (powershell -c `"irm $url -OutFile '$dir\viktor_local.py'`" & echo updated & exit /b)`r`nif `"%~1`"==`"`" (uv run `"$dir\viktor_local.py`" `"%CD%`") else (uv run `"$dir\viktor_local.py`" %*)"
Write-Host "  installed: viktor-local  (next time just run: viktor-local C:\games)"
uv run "$dir\viktor_local.py" (Get-Location).Path
