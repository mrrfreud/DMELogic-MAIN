; DMELogic Installer Script for Inno Setup
; Download Inno Setup from: https://jrsoftware.org/isdl.php

#define MyAppName "DMELogic"
#define MyAppVersion "2.0.24.200"
#define MyAppPublisher "DME Solutions"
#define MyAppExeName "DMELogic.exe"
#define MyAppURL "https://github.com/mrrfreud/DMELogic-Refactored"

[Setup]
AppId={{8F3D5E2A-9B4C-4F1A-8D2E-5C6F7A8B9D0E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
; Per-user install: settings live under %LOCALAPPDATA%\DMELogic, and each user can
; point to shared server folders on first launch.
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=installer_output
OutputBaseFilename=DMELogic_Update_{#MyAppVersion}
SetupIconFile="assets\DMELogic Icon.ico"
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
UninstallDisplayIcon={app}\{#MyAppExeName}
DisableProgramGroupPage=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Main executable and all dependencies from PyInstaller output
Source: "dist\DMELogic\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Assets
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

; Theme files
Source: "theme\*"; DestDir: "{app}\theme"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
; Ensure per-user logs directory exists (app will also create it)
Name: "{localappdata}\DMELogic"; Permissions: users-full
Name: "{localappdata}\DMELogic\Logs"; Permissions: users-full

[Icons]
; Start Menu shortcut
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\assets\DMELogic Icon.ico"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

; Desktop shortcut
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\assets\DMELogic Icon.ico"; Tasks: desktopicon

[Registry]
; Store install metadata (per-user)
Root: HKCU; Subkey: "Software\DMELogic"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\DMELogic"; ValueType: string; ValueName: "Version"; ValueData: "{#MyAppVersion}"; Flags: uninsdeletekey

[Run]
; Option to launch after install
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up old shortcuts if they exist
Type: files; Name: "{autodesktop}\DME Manager Pro.lnk"
Type: files; Name: "{autodesktop}\DmeSolutionsV1.lnk"
Type: files; Name: "{group}\DME Manager Pro.lnk"
































