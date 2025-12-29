; DMELogic Installer Script for Inno Setup
; Download Inno Setup from: https://jrsoftware.org/isdl.php

#define MyAppName "DMELogic"
#define MyAppVersion "2.0.20.132"
#define MyAppPublisher "DME Solutions"
#define MyAppExeName "DMELogic.exe"

[Setup]
AppId={{8F3D5E2A-9B4C-4F1A-8D2E-5C6F7A8B9D0E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=installer_output
OutputBaseFilename=DMELogic_Setup_{#MyAppVersion}
SetupIconFile=assets\DMELogic Icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
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

; Database files (if they exist in installer_data folder)
Source: "installer_data\*.db"; DestDir: "{commonappdata}\DMELogic\Data"; Flags: ignoreversion onlyifdoesntexist; Check: FileExists(ExpandConstant('{src}\installer_data'))

[Dirs]
; Create writable data directory
Name: "{commonappdata}\DMELogic"; Permissions: users-full
Name: "{commonappdata}\DMELogic\Data"; Permissions: users-full
Name: "{commonappdata}\DMELogic\Backups"; Permissions: users-full
Name: "{commonappdata}\DMELogic\Exports"; Permissions: users-full

[Icons]
; Start Menu shortcut
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\assets\DMELogic Icon.ico"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

; Desktop shortcut
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\assets\DMELogic Icon.ico"; Tasks: desktopicon

[Registry]
; Store data directory path
Root: HKLM; Subkey: "Software\DMELogic"; ValueType: string; ValueName: "DataPath"; ValueData: "{commonappdata}\DMELogic\Data"; Flags: uninsdeletekey

[Run]
; Option to launch after install
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up old shortcuts if they exist
Type: files; Name: "{autodesktop}\DME Manager Pro.lnk"
Type: files; Name: "{autodesktop}\DmeSolutionsV1.lnk"
Type: files; Name: "{group}\DME Manager Pro.lnk"

[Code]
function FileExists(FileName: String): Boolean;
begin
  Result := FileOrDirExists(FileName);
end;

procedure CopyDatabaseFiles();
var
  SourcePath, DestPath: String;
  FindRec: TFindRec;
begin
  SourcePath := ExpandConstant('{app}\installer_data');
  DestPath := ExpandConstant('{commonappdata}\DMELogic\Data');
  
  if DirExists(SourcePath) then
  begin
    if FindFirst(SourcePath + '\*.db', FindRec) then
    begin
      try
        repeat
          if not FileExists(DestPath + '\' + FindRec.Name) then
          begin
            FileCopy(SourcePath + '\' + FindRec.Name, DestPath + '\' + FindRec.Name, False);
          end;
        until not FindNext(FindRec);
      finally
        FindClose(FindRec);
      end;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  DataPath: String;
begin
  if CurStep = ssPostInstall then
  begin
    // Create config file pointing to the data directory
    DataPath := ExpandConstant('{commonappdata}\DMELogic\Data');
    SaveStringToFile(ExpandConstant('{app}\data_path.txt'), DataPath, False);
    
    // Copy database files from installer_data to data directory
    CopyDatabaseFiles();
  end;
end;












