# EdTech CJM Generator - Windows launcher (ASCII console output)
$ErrorActionPreference = "Continue"

$Root = $PSScriptRoot
Set-Location $Root

Write-Host "========================================================"
Write-Host "     EdTech CJM Generator"
Write-Host "========================================================"
Write-Host ""

function Refresh-Path {
    $machine = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    $user = [System.Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machine;$user"
}

function Test-PythonCommand {
    param($Python)
    try {
        if ($Python.Exe -match '[\\/]') {
            if (-not (Test-Path -LiteralPath $Python.Exe)) { return $false }
        } elseif (-not (Get-Command $Python.Exe -ErrorAction SilentlyContinue)) {
            return $false
        }

        $allArgs = $Python.Args + @(
            "-c",
            "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"
        )
        & $Python.Exe @allArgs 1>$null 2>$null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Get-PythonVersion {
    param($Python)
    $allArgs = $Python.Args + @(
        "-c",
        "import sys; print(str(sys.version_info[0]) + '.' + str(sys.version_info[1]))"
    )
    $output = & $Python.Exe @allArgs 2>$null
    if ($LASTEXITCODE -ne 0) { return "" }
    return ($output | Select-Object -Last 1).ToString().Trim()
}

function Get-PythonCandidates {
    Refresh-Path

    $items = New-Object System.Collections.ArrayList
    $seen = @{}

    $venvPython = Join-Path $Root ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        $key = "$venvPython|"
        if (-not $seen.ContainsKey($key)) {
            $seen[$key] = $true
            [void]$items.Add(@{ Exe = $venvPython; Args = @() })
        }
    }

    foreach ($entry in @(
            @{ Exe = "python"; Args = @() },
            @{ Exe = "py"; Args = @("-3") }
        )) {
        $key = "$($entry.Exe)|$($entry.Args -join ' ')"
        if (-not $seen.ContainsKey($key)) {
            $seen[$key] = $true
            [void]$items.Add($entry)
        }
    }

    foreach ($line in (& where.exe python 2>$null)) {
        $path = $line.Trim()
        $key = "$path|"
        if ($path -and -not $seen.ContainsKey($key)) {
            $seen[$key] = $true
            [void]$items.Add(@{ Exe = $path; Args = @() })
        }
    }

    foreach ($line in (& py -0p 2>$null)) {
        if ($line -match '([A-Za-z]:\\[^\\]+\\python\.exe)\s*$') {
            $path = $Matches[1].Trim()
            $key = "$path|"
            if (-not $seen.ContainsKey($key)) {
                $seen[$key] = $true
                [void]$items.Add(@{ Exe = $path; Args = @() })
            }
        }
    }

    foreach ($root in @(
            (Join-Path $env:LocalAppData "Programs\Python"),
            "C:\Python314",
            "C:\Python313",
            "C:\Python312",
            "C:\Python311",
            "C:\Python310"
        )) {
        if (-not (Test-Path $root)) { continue }
        $direct = Join-Path $root "python.exe"
        if (Test-Path $direct) {
            $key = "$direct|"
            if (-not $seen.ContainsKey($key)) {
                $seen[$key] = $true
                [void]$items.Add(@{ Exe = $direct; Args = @() })
            }
        }
        foreach ($file in (Get-ChildItem $root -Filter python.exe -Recurse -ErrorAction SilentlyContinue)) {
            $path = $file.FullName
            $key = "$path|"
            if (-not $seen.ContainsKey($key)) {
                $seen[$key] = $true
                [void]$items.Add(@{ Exe = $path; Args = @() })
            }
        }
    }

    return $items
}

function Find-Python {
    foreach ($item in (Get-PythonCandidates)) {
        if (Test-PythonCommand $item) {
            return $item
        }
    }
    return $null
}

function Invoke-Python {
    param($Python, [string[]]$ScriptArgs)
    & $Python.Exe @($Python.Args + $ScriptArgs)
}

function Show-PythonMissingHelp {
    Write-Host ""
    Write-Host "[ERROR] Python 3.10+ is required but was not found." -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Python manually:"
    Write-Host "  https://www.python.org/downloads/"
    Write-Host ""
    Write-Host 'During setup, enable "Add Python to PATH".'
    Write-Host "Then close this window and run run_windows.bat again."
    exit 1
}

$python = Find-Python
if (-not $python) {
    Show-PythonMissingHelp
}

$pyVer = Get-PythonVersion $python
if (-not $pyVer) {
    Show-PythonMissingHelp
}
Write-Host "[OK] Python $pyVer"

$venvPython = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "[INFO] Creating virtual environment .venv ..."
    Invoke-Python $python @("-m", "venv", ".venv")
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to create .venv" -ForegroundColor Red
        exit 1
    }
}

Write-Host "[INFO] Upgrading pip..."
& $venvPython -m pip install --upgrade pip setuptools wheel -q
if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARN] pip upgrade failed, continuing..."
}

Write-Host "[INFO] Installing dependencies from requirements.txt ..."
Write-Host "       (first run may take 1-3 minutes)"
& $venvPython -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to install dependencies." -ForegroundColor Red
    Write-Host "Check your internet connection and try again."
    exit 1
}

$outputDir = Join-Path $Root "output"
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir | Out-Null
}

Write-Host ""
Write-Host "[INFO] Freeing port 5050 if busy..."
Get-NetTCPConnection -LocalPort 5050 -State Listen -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique |
    ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }

Write-Host ""
Write-Host "[OK] Starting server: http://127.0.0.1:5050"
Write-Host "     Browser will open when the server is ready."
Write-Host ""
Write-Host "     Press Ctrl+C in this window to stop the server."
Write-Host "========================================================"
Write-Host ""

$env:CJM_LAUNCHER = "1"

$browserJob = Start-Job -ScriptBlock {
    param($Url)
    for ($i = 0; $i -lt 40; $i++) {
        Start-Sleep -Milliseconds 500
        try {
            $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
            if ($r.StatusCode -eq 200) {
                Start-Process $Url
                return
            }
        } catch {
            continue
        }
    }
} -ArgumentList "http://127.0.0.1:5050"

try {
    & $venvPython (Join-Path $Root "run.py")
} finally {
    Stop-Job $browserJob -ErrorAction SilentlyContinue
    Remove-Job $browserJob -Force -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "Server stopped."
