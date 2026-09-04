#!/usr/bin/env bash
# ============================================================
# Push auto-money-agent to GitHub and enable Pages.
# Run from the repository root: bash push_to_github.sh
# ============================================================

set -e

# ---- 1. Sanity checks ----
if ! command -v git &> /dev/null; then
  echo "❌ git not found. Install from https://git-scm.com"
  exit 1
fi

# ---- 2. Identity (use existing global if set) ----
if [ -z "$(git config --global user.name)" ]; then
  echo "git user.name not set. We'll ask for it once."
  read -p "Your name (e.g. John Smith): " NAME
  git config --global user.name "$NAME"
fi
if [ -z "$(git config --global user.email)" ]; then
  read -p "Your GitHub email: " EMAIL
  git config --global user.email "$EMAIL"
fi

# ---- 3. Repo target ----
read -p "GitHub username (e.g. haine2024): " GH_USER
read -p "Repo name on GitHub (e.g. auto-money-agent): " REPO

REPO_URL="git@github.com:${GH_USER}/${REPO}.git"

# ---- 4. Ensure init + first commit ----
if [ ! -d .git ]; then
  echo "→ git init"
  git init
  git checkout -B main 2>/dev/null || git branch -M main
else
  git branch -M main
fi

# ---- 5. Stage ----
echo "→ git add ."
git add .

if git diff --cached --quiet; then
  echo "→ No changes to commit (already clean)"
else
  echo "→ git commit"
  git commit -m "init: tool station pipeline + 3 demo tools"
fi

# ---- 6. Remote ----
if git remote get-url origin >/dev/null 2>&1; then
  echo "→ Remote 'origin' already exists: $(git remote get-url origin)"
  echo "   (re-run with --reset-origin if you want to switch)"
else
  echo "→ Adding origin: $REPO_URL"
  git remote add origin "$REPO_URL"
fi

# ---- 7. Push ----
echo "→ git push -u origin main"
git push -u origin main

cat <<EOF

✅ Pushed.

Next steps (one-time, in GitHub UI):
  1. Open https://github.com/${GH_USER}/${REPO}/settings/pages
  2. Source: "GitHub Actions"
  3. Wait ~60s. Action will deploy to:
       https://${GH_USER}.github.io/${REPO}/

Optional: pin the live URL locally
  echo "https://${GH_USER}.github.io/${REPO}/" > LIVE_URL.txt
EOF
