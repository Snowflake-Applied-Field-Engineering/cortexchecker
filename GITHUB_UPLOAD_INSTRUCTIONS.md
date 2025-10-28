# GitHub Upload Instructions

## Step-by-Step Guide to Upload Cortex Checker to GitHub

### Prerequisites
- GitHub account with access to the repository
- Git installed on your machine
- Terminal/Command Line access

---

## Step 1: Open Terminal

Open your terminal and navigate to the project directory:

```bash
cd /Users/phorrigan/cortexdemocode
```

---

## Step 2: Initialize Git Repository

Run these commands one by one:

```bash
# Initialize git (if not already done)
git init

# Check status
git status
```

**Expected output:** You should see a list of untracked files in red.

---

## Step 3: Add Remote Repository

```bash
# Add the GitHub repository as remote
git remote add origin https://github.com/Snowflake-Applied-Field-Engineering/cortexchecker.git

# Verify remote was added
git remote -v
```

**Expected output:**
```
origin  https://github.com/Snowflake-Applied-Field-Engineering/cortexchecker.git (fetch)
origin  https://github.com/Snowflake-Applied-Field-Engineering/cortexchecker.git (push)
```

---

## Step 4: Stage All Files

```bash
# Add all files to staging
git add .

# Check what will be committed
git status
```

**Expected output:** Files should now be in green (staged for commit).

---

## Step 5: Commit Changes

```bash
# Commit with a message
git commit -m "Initial commit: Cortex Analyst Role Access Checker v2.1.0"
```

**Expected output:** Summary of files changed and insertions.

---

## Step 6: Set Main Branch

```bash
# Rename branch to main (GitHub standard)
git branch -M main
```

---

## Step 7: Push to GitHub

```bash
# Push to GitHub
git push -u origin main
```

**What happens:**
- You may be prompted for GitHub credentials
- If you have 2FA enabled, you'll need a Personal Access Token (not your password)

**Expected output:**
```
Enumerating objects: XX, done.
Counting objects: 100% (XX/XX), done.
...
To https://github.com/Snowflake-Applied-Field-Engineering/cortexchecker.git
 * [new branch]      main -> main
```

---

## Troubleshooting

### Issue: "Authentication failed"

**Solution:** Use a Personal Access Token instead of password

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token with `repo` scope
3. Use token as password when prompted

### Issue: "Remote already exists"

```bash
# Remove existing remote
git remote remove origin

# Add it again
git remote add origin https://github.com/Snowflake-Applied-Field-Engineering/cortexchecker.git
```

### Issue: "Repository not empty"

If the repository already has content:

```bash
# Pull first, then push
git pull origin main --allow-unrelated-histories
git push -u origin main
```

---

## Verify Upload

After pushing, visit:
https://github.com/Snowflake-Applied-Field-Engineering/cortexchecker

You should see all your files!

---

## Quick Command Summary

Copy and paste these commands in order:

```bash
cd /Users/phorrigan/cortexdemocode
git init
git remote add origin https://github.com/Snowflake-Applied-Field-Engineering/cortexchecker.git
git add .
git commit -m "Initial commit: Cortex Analyst Role Access Checker v2.1.0"
git branch -M main
git push -u origin main
```

---

## What Gets Uploaded

✅ **Included:**
- CortexRoleTool/ (all files)
- README.md
- LICENSE
- .gitignore
- requirements.txt
- setup.sql
- env.example

❌ **Excluded (via .gitignore):**
- .env files
- __pycache__/
- *.pyc
- .DS_Store
- Virtual environments

---

## Next Steps After Upload

1. ✅ Verify files on GitHub
2. ✅ Check README displays correctly
3. ✅ Test clone from another location
4. ✅ Add collaborators if needed
5. ✅ Set up branch protection rules (optional)

---

**Need Help?** 
- GitHub Docs: https://docs.github.com/en/get-started
- Git Docs: https://git-scm.com/doc

