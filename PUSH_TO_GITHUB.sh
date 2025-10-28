#!/bin/bash

# Script to push Cortex Checker to GitHub
# Repository: https://github.com/Snowflake-Applied-Field-Engineering/cortexchecker.git

echo "=========================================="
echo "Pushing Cortex Checker to GitHub"
echo "=========================================="
echo ""

# Navigate to project directory
cd "$(dirname "$0")"

# Initialize git if not already done
if [ ! -d ".git" ]; then
    echo "Initializing Git repository..."
    git init
    echo "✓ Git initialized"
else
    echo "✓ Git repository already initialized"
fi

# Add remote if not already added
if ! git remote | grep -q "origin"; then
    echo "Adding remote origin..."
    git remote add origin https://github.com/Snowflake-Applied-Field-Engineering/cortexchecker.git
    echo "✓ Remote added"
else
    echo "✓ Remote already configured"
    git remote -v
fi

# Stage all files
echo ""
echo "Staging files..."
git add .
echo "✓ Files staged"

# Show status
echo ""
echo "Git status:"
git status

# Commit
echo ""
read -p "Enter commit message (or press Enter for default): " commit_msg
if [ -z "$commit_msg" ]; then
    commit_msg="Initial commit: Cortex Analyst Role Access Checker v2.1.0"
fi

git commit -m "$commit_msg"
echo "✓ Changes committed"

# Push to GitHub
echo ""
echo "Pushing to GitHub..."
echo "You may be prompted for your GitHub credentials."
echo ""

git branch -M main
git push -u origin main

echo ""
echo "=========================================="
echo "✓ Successfully pushed to GitHub!"
echo "=========================================="
echo ""
echo "Repository: https://github.com/Snowflake-Applied-Field-Engineering/cortexchecker"
echo ""

