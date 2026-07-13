; Inno Setup script — builds DrosophilaActivityGUI-Setup.exe from the
; PyInstaller onedir output in ..\dist. Compile from the repo root:
;   iscc windows\installer.iss

#define AppName "Drosophila Activity Analysis GUI"
#define AppVersion "1.0.0"
#define ExeName "DrosophilaActivityGUI.exe"

[Setup]
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Derivative of williamrowell/drosophila_activity_analysis
DefaultDirName={autopf}\DrosophilaActivityGUI
DefaultGroupName={#AppName}
UninstallDisplayIcon={app}\{#ExeName}
OutputBaseFilename=DrosophilaActivityGUI-Setup
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
; paths below are relative to this SourceDir (the repo root)
SourceDir=..
OutputDir=installer_output

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "dist\DrosophilaActivityGUI\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#ExeName}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#ExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#ExeName}"; Description: "Launch the app now"; Flags: nowait postinstall skipifsilent
