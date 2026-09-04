#!/usr/bin/env bash
# ============================================================
# set up GitHub authentication (PAT stored in Windows Credential
# Manager / macOS keychain / Linux git credential cache)
# ============================================================
# This script does NOT store or echo the PAT anywhere on disk.
# You type it once when git prompts you; subsequent git push /
# pull / fetch will pull it from the OS keystore automatically.
# ============================================================

set -e

cd "$(dirname "$0")/.."

echo "=== GitHub auth helper ==="
echo
echo "We'll configure git so your PAT is remembered by the OS."
echo
echo "Step 1 — make sure the remote uses HTTPS (not SSH)"
echo "Step 2 — set the git credential helper (Windows / macOS / Linux auto-detect)"
echo "Step 3 — push once; you'll be prompted for username + PAT"
echo

# Step 1: HTTPS remote
read -p "GitHub username (e.g. hainei0318): " GH_USER
read -p "Repo name on GitHub (e.g. tool-station): " REPO

REPO_URL="https://github.com/${GH_USER}/${REPO}.git"
echo
echo "Setting remote → $REPO_URL"
git remote remove origin 2>/dev/null || true
git remote add origin "$REPO_URL"

# Step 2: pick credential helper
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
  echo "Detected Windows → using Windows Credential Manager."
  git config --global credential.helper manager
elif [[ "$OSTYPE" == "darwin"* ]]; then
  echo "Detected macOS → using keychain."
  git config --global credential.helper osxkeychain
else
  echo "Detected Linux → using 1-hour cache."
  git config --global credential.helper "cache --timeout=3600"
fi

echo
echo "=== Ready to push ==="
echo "When prompted:"
echo "  Username: $GH_USER"
echo "  Password: <paste your PAT; cursor will not move while typing>"
echo

read -p "Push now? [Y/n]: " PUSH
PUSH=${PUSH:-Y}
if [[ "$PUSH" =~ ^[Yy]$ ]]; then
  git push -u origin main
  echo
  echo "✅ Pushed. If this is your first push to a brand-new repo, it works!"
else
  echo "Skipped. Run this when ready:  git push -u origin main"
fi
