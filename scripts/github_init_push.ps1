param(
    [Parameter(Mandatory=$true)]
    [string]$RemoteUrl
)

git init
git branch -M main
git add .
git commit -m "Initial ETIDS Docker data science pipeline"

$origin = git remote get-url origin 2>$null
if ($LASTEXITCODE -eq 0) {
    git remote set-url origin $RemoteUrl
} else {
    git remote add origin $RemoteUrl
}

git push -u origin main
Write-Host "Done. Repository pushed to $RemoteUrl"
