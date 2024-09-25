<h1 align="center">XXMI Installer</h1>

<h4 align="center">Installation tool for XXMI Launcher</h4>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#supported-model-importers">Supported Model Importers</a> •
  <a href="#license">License</a>
</p>

## Disclaimers

- **In-Dev Warning** — **GIMI** and **SRMI** packages are **in-dev** versions, feel free to test but please be aware!

- **Paranoia Warning** — Some picky AVs may be triggered by XXMI .exe or .dll files. Installer and Launcher are unsigned python apps compiled with Pyinstaller, that is [known to have false positives](https://discuss.python.org/t/pyinstaller-false-positive/43171). DLLs are unsigned binaries intended to inject or be injected into the game process, and it doesn't help either. We can't do anything about it, so it's up to you to use them as is, build yourself or go by.

## Features  

- **Automatic Installation** — Fully automatic XXMI Launcher installation

![xxmi-installer](https://github.com/SpectrumQT/XXMI-Installer/blob/main/public-media/XXMI%20Installer.png)

## Installation

1. Install [the latest Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170) ([direct download](https://aka.ms/vs/17/release/vc_redist.x64.exe))
2. Download the [latest release](https://github.com/SpectrumQT/XXMI-Installer/releases/latest) of **XXMI-Installer-vX.X.X.exe**
3. Run **XXMI-Installer-vX.X.X.exe** with Double-Click.
4. Click **[Quick Installation]** to download and install **[XXMI Launcher](https://github.com/SpectrumQT/XXMI-Launcher)**.
5. Once installation is complete, **XXMI Launcher** window will open and install **XXMI** automatically.

## Supported Model Importers

- [WWMI - Wuthering Waves Model Importer GitHub](https://github.com/SpectrumQT/WWMI)
- [ZZMI - Zenless Zone Zero Model Importer GitHub](https://github.com/leotorrez/ZZ-Model-Importer)
- [SRMI - Honkai: Star Rail Model Importer GitHub](https://github.com/SilentNightSound/SR-Model-Importer)
- [GIMI - Genshin Impact Model Importer GitHub](https://github.com/SilentNightSound/GI-Model-Importer)
  
## License

XXMI Installer is licensed under the [GPLv3 License](https://github.com/SpectrumQT/XXMI-Installer/blob/main/LICENSE).
