param(
    [switch]$SkipFFmpeg,
    [switch]$DownloadWhisperModel,
    [string]$WhisperModel = "base",
    [string]$DraftRoot = "F:/Media/02_剪映草稿"
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
    Copy-Item ".env.example" ".env"
    Write-Host "[setup] Created .env from .env.example. Review local paths before production use."
}

function Set-EnvValue {
    param(
        [string]$Path,
        [string]$Key,
        [string]$Value
    )

    if (-not (Test-Path $Path)) {
        New-Item -ItemType File -Path $Path | Out-Null
    }

    $lines = Get-Content -Path $Path -Encoding UTF8
    $updated = $false
    $next = foreach ($line in $lines) {
        if ($line -match "^\s*$([regex]::Escape($Key))=") {
            "$Key=$Value"
            $updated = $true
        } else {
            $line
        }
    }
    if (-not $updated) {
        $next += "$Key=$Value"
    }
    Set-Content -Path $Path -Value $next -Encoding UTF8
}

function Invoke-WithRetry {
    param(
        [scriptblock]$Action,
        [string]$Name,
        [int]$Retries = 3,
        [int]$DelaySeconds = 5
    )

    for ($attempt = 1; $attempt -le $Retries; $attempt++) {
        try {
            & $Action
            return
        } catch {
            if ($attempt -eq $Retries) {
                throw
            }
            Write-Host "[setup] $Name failed on attempt $attempt/$Retries. Retrying in $DelaySeconds seconds..."
            Start-Sleep -Seconds $DelaySeconds
        }
    }
}

if ($DraftRoot) {
    New-Item -ItemType Directory -Force -Path $DraftRoot | Out-Null
    Set-EnvValue -Path ".env" -Key "JIANYING_DRAFT_ROOT" -Value $DraftRoot
    Set-EnvValue -Path ".env" -Key "JIAN_YING_PROJECT_DIR" -Value $DraftRoot
    Write-Host "[setup] Jianying draft root: $DraftRoot"
}

$python = Get-Command py -ErrorAction SilentlyContinue
if ($python) {
    py -3.11 -m venv .venv
} else {
    python -m venv .venv
}

$wheelDir = Join-Path $Root "vendor\wheels"
$hasWheelhouse = (Test-Path $wheelDir) -and ((Get-ChildItem -Path $wheelDir -Filter "*.whl" -ErrorAction SilentlyContinue | Measure-Object).Count -gt 0)
if ($hasWheelhouse) {
    Write-Host "[setup] Installing Python dependencies from local wheelhouse."
    & ".\.venv\Scripts\python.exe" -m pip install --no-index --find-links $wheelDir -r requirements.txt
} else {
    Invoke-WithRetry -Name "pip upgrade" -Action {
        & ".\.venv\Scripts\python.exe" -m pip install --upgrade pip --retries 5 --timeout 120
    }
    Invoke-WithRetry -Name "dependency install" -Retries 5 -Action {
        & ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt --retries 5 --timeout 120
    }
}

if (-not $SkipFFmpeg) {
    $ffmpegExe = Join-Path $Root "vendor\ffmpeg\bin\ffmpeg.exe"
    $ffprobeExe = Join-Path $Root "vendor\ffmpeg\bin\ffprobe.exe"
    if (-not (Test-Path $ffmpegExe) -or -not (Test-Path $ffprobeExe)) {
        $localFFmpeg = "D:\soft\ffmpeg\bin\ffmpeg.exe"
        $localFFprobe = "D:\soft\ffmpeg\bin\ffprobe.exe"
        $vendor = Join-Path $Root "vendor"
        New-Item -ItemType Directory -Force -Path $vendor | Out-Null
        New-Item -ItemType Directory -Force -Path (Join-Path $Root "vendor\ffmpeg\bin") | Out-Null

        $localArchive = Join-Path $vendor "ffmpeg-release-essentials.zip"

        if ((Test-Path $localFFmpeg) -and (Test-Path $localFFprobe)) {
            Write-Host "[setup] Copying FFmpeg from D:\soft\ffmpeg..."
            Copy-Item -LiteralPath $localFFmpeg -Destination $ffmpegExe -Force
            Copy-Item -LiteralPath $localFFprobe -Destination $ffprobeExe -Force
        } else {
            $download = Join-Path $vendor "ffmpeg-release-essentials.zip"
            $extract = Join-Path $vendor "ffmpeg_extract"
            if (Test-Path $extract) {
                Remove-Item -LiteralPath $extract -Recurse -Force
            }
            if (Test-Path $localArchive) {
                Write-Host "[setup] Extracting FFmpeg from local vendor archive."
            } else {
                Write-Host "[setup] Downloading FFmpeg..."
                Invoke-WithRetry -Name "FFmpeg download" -Retries 5 -DelaySeconds 10 -Action {
                    Invoke-WebRequest `
                        -Uri "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" `
                        -OutFile $download
                }
            }
            Expand-Archive -Path $download -DestinationPath $extract -Force
            $bin = Get-ChildItem -Path $extract -Recurse -Directory -Filter "bin" |
                Where-Object { Test-Path (Join-Path $_.FullName "ffmpeg.exe") } |
                Select-Object -First 1
            if (-not $bin) {
                throw "FFmpeg download did not contain ffmpeg.exe"
            }
            Copy-Item -LiteralPath (Join-Path $bin.FullName "ffmpeg.exe") -Destination $ffmpegExe -Force
            Copy-Item -LiteralPath (Join-Path $bin.FullName "ffprobe.exe") -Destination $ffprobeExe -Force
            if (-not (Test-Path $localArchive)) {
                Remove-Item -LiteralPath $download -Force
            }
            Remove-Item -LiteralPath $extract -Recurse -Force
        }
    }
    Set-EnvValue -Path ".env" -Key "FFMPEG_PATH" -Value "vendor/ffmpeg/bin/ffmpeg.exe"
    Set-EnvValue -Path ".env" -Key "FFPROBE_PATH" -Value "vendor/ffmpeg/bin/ffprobe.exe"
    Write-Host "[setup] FFmpeg ready."
}

if ($DownloadWhisperModel) {
    Write-Host "[setup] Pre-downloading faster-whisper model: $WhisperModel"
    $env:HF_HOME = Join-Path $Root "vendor\hf-cache"
    $env:WHISPER_MODEL = $WhisperModel
    & ".\.venv\Scripts\python.exe" -c "from faster_whisper.utils import download_model; import os; print(download_model(os.environ.get('WHISPER_MODEL', 'base')))"
}

Write-Host "[setup] Done."
Write-Host "[setup] Edit .env, then run .\run_webui.ps1"
