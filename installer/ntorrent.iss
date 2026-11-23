; NTorrent Windows installer script (Inno Setup 6)
;
; Build order:
;   1. pyinstaller --noconsole --onefile --name NTorrent --collect-all libtorrent main.py
;      (run from the project root -- produces dist\NTorrent.exe)
;   2. Compile this script:
;      "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\ntorrent.iss
;   3. Output: installer\Output\NTorrent-Setup.exe

#define MyAppName "NTorrent"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "NengzXGODZ"
#define MyAppURL "https://github.com/NengzXGODZ"
#define MyAppExeName "NTorrent.exe"

[Setup]
AppId={{B7E2B9E4-6B1A-4E7D-9E2A-9C7B6A1F2D3E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=NTorrent-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "fileassoc"; Description: "Associate .torrent files with {#MyAppName}"; GroupDescription: "Other:"; Flags: unchecked

[Files]
; Path is relative to this .iss file, i.e. ..\dist\NTorrent.exe from installer\
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; Only written if the user ticks "fileassoc" above.
Root: HKCU; Subkey: "Software\Classes\.torrent"; ValueType: string; ValueName: ""; ValueData: "NTorrent.Torrent"; Flags: uninsdeletevalue; Tasks: fileassoc
Root: HKCU; Subkey: "Software\Classes\NTorrent.Torrent"; ValueType: string; ValueName: ""; ValueData: "BitTorrent File"; Flags: uninsdeletekey; Tasks: fileassoc
Root: HKCU; Subkey: "Software\Classes\NTorrent.Torrent\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"; Tasks: fileassoc
Root: HKCU; Subkey: "Software\Classes\NTorrent.Torrent\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: fileassoc

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
