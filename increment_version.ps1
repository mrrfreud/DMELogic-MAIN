# Increment version in installer_script.iss
$content = Get-Content 'installer_script.iss' -Raw
if ($content -match '#define MyAppVersion "([^"]+)"') {
    $ver = $matches[1]
    $parts = $ver.Split('.')
    $parts[3] = [int]$parts[3] + 1
    $newVer = $parts -join '.'
    $content -replace '#define MyAppVersion "[^"]+"', ('#define MyAppVersion "' + $newVer + '"') | Set-Content 'installer_script.iss'
    Write-Output $newVer
}
