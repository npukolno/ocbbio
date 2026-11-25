# viktor-local for Windows: irm https://ocb2016.me/viktor-local/install.ps1 | iex
$url = if ($env:VIKTOR_LOCAL_URL) { $env:VIKTOR_LOCAL_URL } else { "https://ocb2016.me/viktor-local/viktor_local.py" }
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { irm https://astral.sh/uv/install.ps1 | iex; $env:Path = "$env:USERPROFILE\.local\bin;$env:Path" }
$dir = "$env:USERPROFILE\.cache\viktor-local"; New-Item -ItemType Directory -Force $dir | Out-Null
irm $url -OutFile "$dir\viktor_local.py"
uv run "$dir\viktor_local.py" (Get-Location).Path
