import PyInstaller.__main__
import os
import shutil

# Clean previous builds
if os.path.exists("dist"): shutil.rmtree("dist")
if os.path.exists("build"): shutil.rmtree("build")

# Get path to customtkinter to include data
import customtkinter
ctk_path = os.path.dirname(customtkinter.__file__)

# Define separator for --add-data (semicolon for Windows)
sep = ";" if os.name == 'nt' else ":"

PyInstaller.__main__.run([
    'src/main.py',
    '--name=GitHubManagerPro',
    '--onefile',
    '--noconsole',
    f'--add-data={ctk_path}{sep}customtkinter',  # Include CustomTkinter themes
    f'--add-data=denastech.png{sep}.',           # Include Icon
    '--icon=denastech.png',
    '--hidden-import=PIL._tkinter_finder',       # Common issue with Pillow
    '--clean'
])

print("\nBuild Complete! Check 'dist/' folder for GitHubManagerPro.exe")
