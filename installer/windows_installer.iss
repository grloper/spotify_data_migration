; Inno Setup Script for Spotify Data Migration
; This script creates a Windows installer for the application

#define MyAppName "Spotify Data Migration"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "grloper"
#define MyAppURL "https://github.com/grloper/spotify_data_migration"
#define MyAppExeName "spotify_data_migration.exe"

[Setup]
; Application info
AppId={{A4BD1F92-F1EA-4F95-8D3F-32D02E9DFD71}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Default installation directory
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=.\output
OutputBaseFilename=SpotifyDataMigration-Setup-v{#MyAppVersion}

; Compression settings
Compression=lzma
SolidCompression=yes

; UI settings
WizardStyle=modern
LicenseFile=..\LICENSE

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Include the main executable and all required files
Source: "..\dist\spotify_data_migration\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\spotify_data_migration\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
