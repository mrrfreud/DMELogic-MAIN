; DMELogic USB Installer Script for Inno Setup
; Creates a plug-and-play installer for USB deployment
; First run will prompt user to configure server folder locations

#define MyAppName "DMELogic"
#define MyAppVersion "2.0.20.133"
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
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; Output to installer_output folder
OutputDir=installer_output
OutputBaseFilename=DMELogic_Setup_{#MyAppVersion}_USB
SetupIconFile=assets\DMELogic Icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#MyAppExeName}
DisableProgramGroupPage=yes
; Show license if exists
; LicenseFile=LICENSE.txt
; Show info before install
InfoBeforeFile=INSTALL_INFO.txt
; Estimated size
DiskSpanning=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Messages]
WelcomeLabel1=Welcome to the [name] Setup Wizard
WelcomeLabel2=This will install [name/ver] on your computer.%n%nIMPORTANT: On first launch, you will be prompted to configure the server folder locations for your databases and documents.%n%nIt is recommended that you close all other applications before continuing.

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Main executable and all dependencies from PyInstaller output
Source: "dist\DMELogic\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Assets folder (icons, images, templates)
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

; Theme files
Source: "theme\*"; DestDir: "{app}\theme"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
; Create local app data directory for logs
Name: "{localappdata}\DMELogic"; Permissions: users-full
Name: "{localappdata}\DMELogic\Logs"; Permissions: users-full

[Icons]
; Start Menu shortcuts
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\assets\DMELogic Icon.ico"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

; Desktop shortcut (checked by default)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\assets\DMELogic Icon.ico"; Tasks: desktopicon

[Registry]
; Store app installation path for reference
Root: HKLM; Subkey: "Software\DMELogic"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\DMELogic"; ValueType: string; ValueName: "Version"; ValueData: "{#MyAppVersion}"; Flags: uninsdeletekey

[Run]
; Launch after install (checked by default)
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up old shortcuts from previous versions if they exist
Type: files; Name: "{autodesktop}\DME Manager Pro.lnk"
Type: files; Name: "{autodesktop}\DmeSolutionsV1.lnk"
Type: files; Name: "{group}\DME Manager Pro.lnk"

[Code]
// Custom wizard page for server connection info
var
  InfoPage: TWizardPage;
  InfoMemo: TMemo;

procedure InitializeWizard;
begin
  // Create custom info page
  InfoPage := CreateCustomPage(wpWelcome, 'Network Configuration Required', 
    'Important information about first-time setup');
  
  InfoMemo := TMemo.Create(InfoPage);
  InfoMemo.Parent := InfoPage.Surface;
  InfoMemo.Left := 0;
  InfoMemo.Top := 0;
  InfoMemo.Width := InfoPage.SurfaceWidth;
  InfoMemo.Height := InfoPage.SurfaceHeight;
  InfoMemo.ScrollBars := ssVertical;
  InfoMemo.ReadOnly := True;
  InfoMemo.WordWrap := True;
  InfoMemo.Lines.Add('FIRST-TIME SETUP WIZARD');
  InfoMemo.Lines.Add('');
  InfoMemo.Lines.Add('When you first launch DMELogic, a setup wizard will guide you through configuring your server connections.');
  InfoMemo.Lines.Add('');
  InfoMemo.Lines.Add('You will need to know the paths to:');
  InfoMemo.Lines.Add('');
  InfoMemo.Lines.Add('1. DATABASE FOLDER');
  InfoMemo.Lines.Add('   Where patient and order databases are stored.');
  InfoMemo.Lines.Add('   Example: \\SERVER\DMEData\Databases');
  InfoMemo.Lines.Add('');
  InfoMemo.Lines.Add('2. FAX DOCUMENTS FOLDER');
  InfoMemo.Lines.Add('   Where scanned/faxed documents (PDFs) are stored.');
  InfoMemo.Lines.Add('   Example: \\SERVER\DMEData\Faxes');
  InfoMemo.Lines.Add('');
  InfoMemo.Lines.Add('3. BACKUP FOLDER (Optional)');
  InfoMemo.Lines.Add('   Where automatic backups will be saved.');
  InfoMemo.Lines.Add('   Example: \\SERVER\DMEData\Backups');
  InfoMemo.Lines.Add('');
  InfoMemo.Lines.Add('Please contact your IT administrator if you are unsure about these paths.');
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Nothing needed - first run wizard handles configuration
  end;
end;
