@echo off
cloc.exe --out=lines.txt --exclude-list-file=ignore.txt --force-lang="C++","pde" --quiet --exclude-dir=.git .
python py/control.py
pause