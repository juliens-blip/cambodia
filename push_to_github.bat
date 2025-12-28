@echo off
echo Closing Claude Code and pushing to GitHub...
echo.

REM Remove the lock file
if exist ".git\index.lock" del /F ".git\index.lock"

REM Stage all files
git add .

REM Create initial commit
git commit -m "first commit" -m "" -m "🤖 Generated with [Claude Code](https://claude.com/claude-code)" -m "" -m "Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

REM Ensure main branch
git branch -M main

REM Push to GitHub
git push -u origin main

echo.
echo Done! Project pushed to https://github.com/juliens-blip/cambodia.git
pause
