@echo off
title Commit EMC Tools to GitHub
git add .
echo Write your message for the commit:
set /p message=
git commit -m "%message%"
git push -u origin master
pause
exit