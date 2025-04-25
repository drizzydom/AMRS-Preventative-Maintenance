; AMRS Maintenance Tracker - Installer Script for Inno Setup
; This script will create a Windows installer for the AMRS Maintenance Tracker application

#define MyAppName "AMRS Maintenance Tracker"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "AMRS Technologies"
#define MyAppURL "https://example.com/amrs-maintenance"
#define MyAppExeName "MaintenanceTracker.exe"
#define MyAppAssocName MyAppName + " File"
#define MyAppAssocExt ".amrs"
#define MyAppAssocKey StringChange(MyAppAssocName, " ", "") + MyAppAssocExt

[Setup]
; Basic setup information
AppId={{9DE32717-F7D9-4AF4-B762-9D4951A548C1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
ChangesAssociations=yes
DisableProgramGroupPage=yes
; Compression options - best compression
Compression=lzma
SolidCompression=yes
; UI options
WizardStyle=modern
SetupIconFile=..\resources\app_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Main application executable and resources
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Data folder (create empty if not exists)
Source: "*"; DestDir: "{localappdata}\AMRS-Maintenance-Tracker\data"; Flags: uninsneveruninstall skipifsourcedoesntexist

; Add additional files like documentation
Source: "..\..\README.md"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "..\..\LICENSE"; DestDir: "{app}\docs"; Flags: ignoreversion

[Dirs]
; Create directories that should persist after uninstallation
Name: "{localappdata}\AMRS-Maintenance-Tracker"; Flags: uninsneveruninstall
Name: "{localappdata}\AMRS-Maintenance-Tracker\data"; Flags: uninsneveruninstall
Name: "{localappdata}\AMRS-Maintenance-Tracker\logs"; Flags: uninsneveruninstall
Name: "{localappdata}\AMRS-Maintenance-Tracker\reports"; Flags: uninsneveruninstall

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Registry]
; Register file association
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocExt}\OpenWithProgids"; ValueType: string; ValueName: "{#MyAppAssocKey}"; ValueData: ""; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}"; ValueType: string; ValueName: ""; ValueData: "{#MyAppAssocName}"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""
Root: HKA; Subkey: "Software\Classes\Applications\{#MyAppExeName}\SupportedTypes"; ValueType: string; ValueName: ".amrs"; ValueData: ""

; Add app to Windows firewall exceptions
Root: HKA; Subkey: "SOFTWARE\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKA; Subkey: "SOFTWARE\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "Version"; ValueData: "{#MyAppVersion}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// Check for .NET Framework installation
function IsDotNetInstalled(): Boolean;
var
    resultCode: Integer;
begin
    // Check if .NET Framework 4.7.2 or newer is installed
    if not Exec('powershell.exe', '-Command "if((Get-ItemProperty ''HKLM:\SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full'').Release -ge 461808) { exit 0 } else { exit 1 }"', '', SW_HIDE, ewWaitUntilTerminated, resultCode) then
    begin
        Result := False;
    end
    else
    begin
        Result := (resultCode = 0);
    end;
end;

// Check for VC++ Redistributable
function IsVCRedistInstalled(): Boolean;
var
    resultCode: Integer;
begin
    // Check if Visual C++ 2015-2019 Redistributable is installed
    if not Exec('powershell.exe', '-Command "if (Get-ItemProperty -Path ''HKLM:\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64'' -Name ''Installed'' -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"', '', SW_HIDE, ewWaitUntilTerminated, resultCode) then
    begin
        Result := False;
    end
    else
    begin
        Result := (resultCode = 0);
    end;
end;

// This event is triggered when the installer initializes
procedure InitializeWizard;
var
    downloadPage: TDownloadWizardPage;
begin
    // Create download page for prerequisites
    downloadPage := CreateDownloadPage(SetupMessage(msgWizardPreparing), SetupMessage(msgPreparingDesc), nil);
    
    // Check for required prerequisites
    if not IsDotNetInstalled then
    begin
        downloadPage.Add('.NET Framework 4.7.2', 'https://go.microsoft.com/fwlink/?LinkId=863262', 'dotnet-framework-installer.exe', '', '', False, False, '');
    end;
    
    if not IsVCRedistInstalled then
    begin
        downloadPage.Add('Visual C++ Redistributable for Visual Studio 2015-2019', 'https://aka.ms/vs/16/release/vc_redist.x64.exe', 'vc_redist.x64.exe', '', '', False, False, '');
    end;
    
    if downloadPage.Count > 0 then
    begin
        downloadPage.Show;
        downloadPage.Download;
    end;
end;

// This event is triggered when the installer is ready to install
function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
    Result := '';
end;

// This event is triggered when the installation is completed
procedure CurStepChanged(CurStep: TSetupStep);
begin
    if CurStep = ssPostInstall then
    begin
        // Create an initial configuration file if it doesn't exist
        if not FileExists(ExpandConstant('{localappdata}\AMRS-Maintenance-Tracker\config.json')) then
        begin
            SaveStringToFile(ExpandConstant('{localappdata}\AMRS-Maintenance-Tracker\config.json'), '{"firstRun": true, "serverUrl": "http://localhost:10000"}', False);
        end;
    end;
end;
