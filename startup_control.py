"""Current-user Startup launcher. No Task Scheduler, elevation, or policy changes."""
from pathlib import Path
import subprocess

def write_startup_launcher(root,startup_dir,python=None,worker=None):
    root=Path(root).resolve();startup_dir=Path(startup_dir)
    python=Path(python) if python else root/'.venv/Scripts/pythonw.exe'
    worker=Path(worker) if worker else root/'rendered_worker.py'
    if not python.is_file() or not worker.is_file():raise FileNotFoundError('Worker or Python executable missing')
    (root/'logs').mkdir(exist_ok=True);startup_dir.mkdir(parents=True,exist_ok=True)
    def quote(path):
        s=str(path)
        if any(c in s for c in '\r\n"'):raise ValueError('Unsupported launcher path')
        return '"'+s.replace('%','%%')+'"'
    path=startup_dir/'AEDIGITAL Noon Monitor.cmd'
    text='@echo off\r\nsetlocal DisableDelayedExpansion\r\ncd /d '+quote(root)+'\r\nstart "" /b '+quote(python)+' '+quote(worker)+' 1>>'+quote(root/'logs'/'launcher.log')+' 2>&1\r\n'
    # cmd.exe uses the local Windows codepage for batch files.
    path.write_text(text,encoding='mbcs',newline='')
    return path

def start_background(root,python=None,worker=None):
    root=Path(root)
    python=python or root/'.venv/Scripts/pythonw.exe';worker=worker or root/'rendered_worker.py'
    log=(root/'logs'/'launcher.log').open('ab')
    try:
        return subprocess.Popen([str(python),str(worker)],cwd=root,stdin=subprocess.DEVNULL,stdout=log,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    finally:log.close()
