# =============================================================================
#  MUNI-PAL - set one secret into secrets/muni-pal.enc.env  (PowerShell writer)
# =============================================================================
#      .\set-secret.ps1 STRIPE_SECRET_KEY      prompt (hidden) and store
#      .\set-secret.ps1 -List                  show slots, masked
#
#  Laptop-side WRITER, matching CHAMPION SOCIAL/secrets.ps1. The bash twin
#  (set-secret.sh) does the same job from git-bash; use whichever shell you are
#  already in. There is no writer on any other machine.
#
#  KEEP THIS FILE STRICTLY ASCII. Windows PowerShell 5.1 decodes a .ps1 as ANSI
#  unless it carries a UTF-8 BOM, so a stray em-dash or curly quote in a comment
#  turns into mojibake mid-string and cascades into "Unexpected token" parse
#  errors far from the real cause. Champion Social's script is ASCII for the
#  same reason.
#
#  The crypto path is lifted from CHAMPION SOCIAL/secrets.ps1 rather than
#  rewritten, because two PS 5.1 traps make the obvious implementation wrong:
#    * `$text | sops ...` writes stdin through a StreamWriter that emits a UTF-8
#      BOM and appends a CRLF. The BOM fuses onto the FIRST variable name and
#      the CRLF puts a stray \r on the LAST value. Both are invisible on
#      Windows and only surface elsewhere. We write raw bytes to BaseStream.
#    * `sops set` needs the value as a command-line argument, and PS 5.1 cannot
#      reliably pass a string containing a double quote to a native exe. So we
#      re-encrypt the whole file over stdin with --filename-override instead.
# =============================================================================

[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string] $Name,

    # Read the value from an environment variable instead of prompting. For
    # automation only - a prompt is preferable for a human, because an
    # environment variable is readable by every process running as you.
    [string] $FromEnvVar,

    [switch] $List
)

$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$SecretsFile = Join-Path $ProjectRoot 'secrets\muni-pal.enc.env'
$SopsConfig  = Join-Path $ProjectRoot '.sops.yaml'
$Unset       = '__UNSET__'

# Scheduled tasks run without a logon session and do not resolve profile
# defaults. Point at the age identity explicitly.
if (-not $env:SOPS_AGE_KEY_FILE) {
    $env:SOPS_AGE_KEY_FILE = 'C:\Users\st3ja\.config\sops\age\keys.txt'
}

if (-not (Get-Command sops -ErrorAction SilentlyContinue)) {
    throw "sops not found on PATH. Install with: winget install SecretsOPerationS.SOPS"
}
if (-not (Test-Path $SecretsFile)) { throw "Secrets file missing: $SecretsFile" }

function Get-Plain {
    $raw = & sops decrypt $SecretsFile 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $raw) {
        throw "Could not decrypt the secrets file. Is this machine a recipient in .sops.yaml?"
    }
    # Ordered so the file keeps a stable shape across writes instead of
    # reshuffling every save, which would make diffs useless.
    $map   = New-Object System.Collections.Specialized.OrderedDictionary
    $first = $true
    foreach ($line in $raw) {
        $t = "$line".Trim()
        # SOPS on Windows prefixes stdout with a UTF-8 BOM. Strip it explicitly
        # rather than relying on host decoding behaviour.
        if ($first) { $t = $t.TrimStart([char]0xFEFF); $first = $false }
        if ($t -eq '' -or $t.StartsWith('#')) { continue }
        $i = $t.IndexOf('=')
        if ($i -lt 1) { continue }
        $map[$t.Substring(0, $i)] = $t.Substring($i + 1)
    }
    return $map
}

function Write-SopsStdin($text) {
    $sops = (Get-Command sops).Source
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName  = $sops
    $psi.Arguments = 'encrypt --input-type dotenv --output-type dotenv ' +
                     ('--filename-override "{0}" --output "{0}"' -f $SecretsFile)
    $psi.WorkingDirectory       = $ProjectRoot
    $psi.UseShellExecute        = $false
    $psi.RedirectStandardInput  = $true
    $psi.RedirectStandardError  = $true
    $psi.RedirectStandardOutput = $true

    $p = [System.Diagnostics.Process]::Start($psi)
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($text)   # GetBytes emits no BOM
    $p.StandardInput.BaseStream.Write($bytes, 0, $bytes.Length)
    $p.StandardInput.BaseStream.Flush()
    $p.StandardInput.Close()
    $err = $p.StandardError.ReadToEnd()
    $p.WaitForExit()
    if ($p.ExitCode -ne 0) { throw "sops encrypt failed (exit $($p.ExitCode)):`n$err" }
}

function Format-Mask($value) {
    if ($null -eq $value -or $value -eq '') { return '(empty)' }
    if ($value -eq $Unset)                  { return '(not set)' }
    if ($value.Length -le 8)                { return ('*' * $value.Length) }
    return $value.Substring(0, 4) + ('*' * 6) + $value.Substring($value.Length - 4)
}

function Show-List {
    $map = Get-Plain
    Write-Host ''
    Write-Host ('  {0,-30} {1,-10} {2}' -f 'SLOT', 'STATUS', 'PREVIEW')
    Write-Host ('  ' + ('-' * 62))
    foreach ($k in $map.Keys) {
        $status = if ($map[$k] -eq $Unset) { 'not set' } else { 'SET' }
        Write-Host ('  {0,-30} {1,-10} {2}' -f $k, $status, (Format-Mask $map[$k]))
    }
    Write-Host ''
}

if ($List -or -not $Name) {
    Show-List
    if (-not $Name) {
        Write-Host 'Usage: .\set-secret.ps1 <SLOT_NAME>' -ForegroundColor Yellow
    }
    return
}

# ------------------------------------------------------------------ value ----
if ($FromEnvVar) {
    $value = [Environment]::GetEnvironmentVariable($FromEnvVar)
    if (-not $value) { throw "Environment variable '$FromEnvVar' is empty or unset." }
} else {
    # Hidden input via SecureString, converted through a BSTR we zero out.
    $secure = Read-Host -Prompt "Value for $Name (input hidden)" -AsSecureString
    $bstr   = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try     { $value = [Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
}

if (-not $value)            { throw "Empty value, aborting." }
if ($value -match "[`r`n]") { throw "Value contains a newline, which dotenv cannot represent." }
# A stray space or quote almost always means a bad paste, and produces a key
# that authenticates nowhere while looking correct in the masked preview.
if ($value -match '[\s"'']')  { throw "Value contains a space or quote. Check the paste." }

# ---------------------------------------------------------------- persist ----
$backup = [System.IO.File]::ReadAllBytes($SecretsFile)

$map = Get-Plain
$map[$Name] = $value
$text = (($map.Keys | ForEach-Object { "$_=$($map[$_])" }) -join "`n") + "`n"

try {
    Write-SopsStdin $text

    # Prove the round-trip. A file that encrypts but will not decrypt is worse
    # than no change at all, so restore the original if verification fails.
    & sops decrypt $SecretsFile > $null 2>&1
    if ($LASTEXITCODE -ne 0) { throw "File no longer decrypts after write." }

    # Re-encryption regenerates the recipient list from .sops.yaml. Confirm we
    # did not silently drop a reader.
    $pattern  = 'age1' + '[a-z0-9]{20,}'
    $recips   = (Select-String -Path $SecretsFile -Pattern 'sops_age__list_\d+__map_enc').Count
    $expected = (Get-Content $SopsConfig |
                 Where-Object { -not $_.TrimStart().StartsWith('#') -and $_ -match $pattern }).Count
    if ($recips -lt $expected) {
        Write-Host "  WARNING: file has $recips recipient(s) but .sops.yaml lists $expected." -ForegroundColor Yellow
    }

    Write-Host "  OK: $Name set." -ForegroundColor Green
    Show-List
}
catch {
    [System.IO.File]::WriteAllBytes($SecretsFile, $backup)
    Write-Host "  FAILED - original file restored untouched." -ForegroundColor Red
    throw
}
