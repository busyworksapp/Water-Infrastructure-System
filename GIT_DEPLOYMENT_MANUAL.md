# MANUAL GIT DEPLOYMENT GUIDE

Since Git installation requires manual completion, here's the step-by-step process:

## Step 1: Install Git (If Not Done)

**Download**: https://git-scm.com/download/win

1. Run the installer
2. Click through with default options
3. **Important**: Select "Use Git from PowerShell" or "Add Git to PATH"
4. Finish the installation

**Verify Installation**:
```powershell
git --version
# Should show: git version 2.43.0.windows.1
```

---

## Step 2: Initialize Git Repository

Run these commands in PowerShell, one at a time:

```powershell
cd c:\Users\me\Desktop\randwater
```

```powershell
git config --global user.name "Water Infrastructure System"
git config --global user.email "system@waterinfra.dev"
```

```powershell
git init
```

---

## Step 3: Add All Files

```powershell
git add .
```

---

## Step 4: Create Initial Commit

```powershell
git commit -m "Initial commit: National Water Infrastructure Monitoring System - Production Ready"
```

---

## Step 5: Add GitHub Remote

```powershell
git remote add origin https://github.com/busyworksapp/Water-Infrastructure-System.git
```

---

## Step 6: Set Main Branch

```powershell
git branch -M main
```

---

## Step 7: Push to GitHub

```powershell
git push -u origin main
```

**Note**: You'll be prompted for GitHub credentials. Use either:
- GitHub username + personal access token, OR
- SSH key (if you have one configured)

---

## If Push Fails

Try with HTTPS token:
```powershell
git remote set-url origin https://YOUR_GITHUB_USERNAME:YOUR_TOKEN@github.com/busyworksapp/Water-Infrastructure-System.git
git push -u origin main
```

Or use SSH:
```powershell
git remote set-url origin git@github.com:busyworksapp/Water-Infrastructure-System.git
git push -u origin main
```

---

## Verify Success

After pushing:
```powershell
git log --oneline
# Should show your commit

git remote -v
# Should show: origin  https://github.com/busyworksapp/Water-Infrastructure-System.git
```

---

## Next Steps After Git Push

Once code is in GitHub, deploy to Railway:

1. Go to https://railway.app/dashboard
2. Click "New Project"
3. Select "Deploy from GitHub"
4. Authenticate and select Water-Infrastructure-System repo
5. Click "Deploy"
6. Add all environment variables (see IMMEDIATE_DEPLOYMENT_STEPS.md)
7. Monitor deployment logs

**Total time to production: 15-20 minutes**

---

## Troubleshooting

### "git: command not found"
- Git installation didn't complete
- Download and run installer again from: https://git-scm.com/download/win
- Make sure to select "Add Git to PATH" or "Use Git from PowerShell"

### "fatal: not a git repository"
- Make sure you're in the right directory: `cd c:\Users\me\Desktop\randwater`
- Run `git init` first

### "authentication failed"
- Check your GitHub credentials
- Try using personal access token instead of password
- Visit https://github.com/settings/tokens to generate one

### "rejected / non-fast-forward"
- Run: `git pull origin main --allow-unrelated-histories`
- Then: `git push -u origin main`

---

**Status**: Ready to deploy once Git is installed  
**Next**: Follow steps above or use deploy.ps1 script when Git is available
