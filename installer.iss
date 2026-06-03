; Inno Setup script for Ezcel.
; Compile: build_installer.bat  (or open with Inno Setup Compiler).

#define MyAppName "Ezcel"
#define MyAppVersion "0.12.5"
#define MyAppPublisher "EZG"
#define MyAppExeName "Ezcel.exe"

[Setup]
AppId={{A3F5C1E2-9B4D-4E7A-8C21-6D3F0B9E2A14}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Ezcel
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; Per-user install (no admin needed). Change 'lowest' -> 'admin' and
; {autopf} becomes Program Files for an all-users install.
PrivilegesRequired=lowest
OutputDir=installer
OutputBaseFilename=Ezcel-Setup-{#MyAppVersion}
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"
Name: "contextmenu"; Description: "Add ""Open with Ezcel"" to the right-click menu for .csv/.xlsx files"; GroupDescription: "Integration:"; Flags: unchecked

[Files]
; Bundle the whole onedir folder produced by PyInstaller.
Source: "dist\Ezcel\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; Optional: add an "Open with EZG - Excel" entry to the right-click menu
; (does NOT change the default program, so no conflict with Excel).
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.csv\shell\Ezcel"; \
    ValueType: string; ValueData: "Open with Ezcel"; Tasks: contextmenu; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.csv\shell\Ezcel\command"; \
    ValueType: string; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.xlsx\shell\Ezcel"; \
    ValueType: string; ValueData: "Open with Ezcel"; Tasks: contextmenu; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.xlsx\shell\Ezcel\command"; \
    ValueType: string; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: contextmenu

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName} now"; \
    Flags: nowait postinstall skipifsilent
