
$ErrorActionPreference = "Stop"

try {
    Write-Host "Checking Git version..."
    git --version
} catch {
    Write-Error "Git is NOT found. Please restart your terminal or computer."
    exit 1
}

if (-not (Test-Path .git)) {
    Write-Host "Initializing Git..."
    git init
}

Write-Host "Adding files..."
git add .

Write-Host "Committing..."
try {
    git commit -m "UX Upgrade: Animated progress and Info Card"
} catch {
    Write-Host "Nothing to commit or commit failed (might be empty)."
}

Write-Host "Renaming branch to main..."
git branch -M main

Write-Host "Setting remote..."
try {
    git remote add origin https://github.com/mtugrultekin/pocketbooksync_bot.git
} catch {
    Write-Host "Remote origin already exists. Setting URL..."
    git remote set-url origin https://github.com/mtugrultekin/pocketbooksync_bot.git
}

Write-Host "Pushing to GitHub..."
git push -u origin main
