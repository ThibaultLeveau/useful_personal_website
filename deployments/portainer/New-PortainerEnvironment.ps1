[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-z0-9][a-z0-9._-]{0,127}$')]
    [string]$ImageTag,

    [ValidatePattern('^[0-9A-Za-z][0-9A-Za-z._+-]{0,63}$')]
    [string]$BuildVersion = '1.0.0'
)

$ErrorActionPreference = 'Stop'
$deploymentDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$templatePath = Join-Path $deploymentDirectory 'portainer.env.example'
$outputPath = Join-Path $deploymentDirectory 'portainer.env'

if (Test-Path -LiteralPath $outputPath) {
    throw "Refusing to overwrite $outputPath. Move or delete it deliberately first."
}

$commit = (& git -C (Resolve-Path (Join-Path $deploymentDirectory '../..')) rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $commit -notmatch '^[0-9a-f]{40}$') {
    throw 'Unable to read a full lowercase Git commit identifier.'
}

function New-UrlSafeSecret {
    $bytes = [byte[]]::new(48)
    $generator = [Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $generator.GetBytes($bytes)
    }
    finally {
        $generator.Dispose()
    }
    return [Convert]::ToBase64String($bytes).TrimEnd('=').Replace('+', '-').Replace('/', '_')
}

$values = @{
    IMAGE_TAG                        = $ImageTag
    POSTGRES_PASSWORD                = New-UrlSafeSecret
    POSTGRES_MIGRATION_PASSWORD      = New-UrlSafeSecret
    POSTGRES_RUNTIME_PASSWORD        = New-UrlSafeSecret
    POSTGRES_AUDIT_OPERATOR_PASSWORD = New-UrlSafeSecret
    APP_BUILD_VERSION                = $BuildVersion
    APP_BUILD_COMMIT                 = $commit
    APP_CSRF_SIGNING_KEY             = New-UrlSafeSecret
    APP_TOKEN_DIGEST_PEPPER          = New-UrlSafeSecret
    APP_PRIVACY_HMAC_KEY             = New-UrlSafeSecret
}

$content = [IO.File]::ReadAllText($templatePath)
foreach ($entry in $values.GetEnumerator()) {
    $pattern = "(?m)^$([Regex]::Escape($entry.Key))=.*$"
    $content = [Regex]::Replace($content, $pattern, "$($entry.Key)=$($entry.Value)")
}

[IO.File]::WriteAllText($outputPath, $content, [Text.UTF8Encoding]::new($false))
Write-Host "Created ignored Portainer environment file: $outputPath"
Write-Host 'Keep it private and upload it only through Portainer when creating the stack.'
