$ErrorActionPreference = "Stop"

$namespace = "urumi"
$secretName = "mysql-secret"

Write-Host "MySQL Secret creation script"
Write-Host "This script will not overwrite an existing Secret."

$context = kubectl config current-context
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($context)) {
    throw "Cannot determine the Kubernetes context."
}

Write-Host "Current Kubernetes context: $context"
$confirmation = Read-Host "Type the exact context name to confirm"

if ($confirmation -cne $context) {
    throw "Context mismatch. Cancelled."
}

$existing = kubectl --context $context -n $namespace `
    get secret $secretName --ignore-not-found

if ($LASTEXITCODE -ne 0) {
    throw "Unable to check for the existing Secret."
}

if ($existing) {
    throw "Secret already exists. Nothing was changed."
}

$rootSecure = Read-Host "MySQL root password" -AsSecureString
$appSecure = Read-Host "MySQL application password" -AsSecureString

function ConvertTo-PlainText([System.Security.SecureString]$Value) {
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($Value)
    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    }
}

$rootPassword = $null
$appPassword = $null

try {
    $rootPassword = ConvertTo-PlainText $rootSecure
    $appPassword = ConvertTo-PlainText $appSecure

    if ([string]::IsNullOrWhiteSpace($rootPassword) -or
        [string]::IsNullOrWhiteSpace($appPassword)) {
        throw "Passwords cannot be empty."
    }

    $env:MYSQL_ROOT_PASSWORD = $rootPassword
    $env:MYSQL_PASSWORD = $appPassword

    $manifest = kubectl --context $context create secret generic $secretName `
        --namespace $namespace `
        --from-literal=MYSQL_ROOT_PASSWORD="$env:MYSQL_ROOT_PASSWORD" `
        --from-literal=MYSQL_DATABASE=wordpress `
        --from-literal=MYSQL_USER=wordpress `
        --from-literal=MYSQL_PASSWORD="$env:MYSQL_PASSWORD" `
        --dry-run=client -o yaml

    if ($LASTEXITCODE -ne 0) {
        throw "Secret generation failed."
    }

    $manifest | kubectl --context $context create -f -

    if ($LASTEXITCODE -ne 0) {
        throw "Secret creation failed."
    }

    Write-Host "Secret created successfully."
}
finally {
    Remove-Item Env:\MYSQL_ROOT_PASSWORD -ErrorAction SilentlyContinue
    Remove-Item Env:\MYSQL_PASSWORD -ErrorAction SilentlyContinue
    $rootPassword = $null
    $appPassword = $null
    $rootSecure.Dispose()
    $appSecure.Dispose()
}
