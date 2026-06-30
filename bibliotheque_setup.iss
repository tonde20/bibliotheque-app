; Script Inno Setup — Gestion de Bibliothèque
; Dr TONDE Salifou — tonde410@gmail.com

#define AppName "Gestion de Bibliothèque"
#define AppVersion "1.2"
#define AppPublisher "Dr TONDE Salifou"
#define AppContact "tonde410@gmail.com"
#define AppExeName "Bibliotheque.exe"
#define SourceDir "dist\Bibliotheque"

[Setup]
AppId={{B1BL10TH-EQUE-TOND-E410-GMAIL000001}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppContact={#AppContact}
AppComments=Système de gestion de bibliothèque avec licences, abonnements et trésorerie.
DefaultDirName={autopf}\BibliothequeApp
DefaultGroupName={#AppName}
OutputDir=installateur
OutputBaseFilename=BibliothequeSetup_v{#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardResizable=no
DisableWelcomePage=no
LicenseFile=
; Icône de l'installateur (décommentez si vous avez un .ico)
; SetupIconFile=icone.ico
UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\{#AppExeName}
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Créer une icône sur le Bureau"; GroupDescription: "Icônes supplémentaires :"; Flags: unchecked
Name: "startupicon"; Description: "Lancer au démarrage de Windows"; GroupDescription: "Démarrage :"; Flags: unchecked

[Files]
; Tous les fichiers de l'application compilée
Source: "{#SourceDir}\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Raccourci dans le menu Démarrer
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Désinstaller {#AppName}"; Filename: "{uninstallexe}"
; Raccourci sur le bureau (optionnel)
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Registry]
; Lancement au démarrage (optionnel)
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#AppName}"; ValueData: """{app}\{#AppExeName}"""; Flags: uninsdeletevalue; Tasks: startupicon

[Run]
; Proposer de lancer l'app à la fin de l'installation
Filename: "{app}\{#AppExeName}"; Description: "Lancer {#AppName} maintenant"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Supprimer la base de données et les dossiers générés à la désinstallation
; (commenté par défaut pour protéger les données — décommentez si souhaité)
; Type: filesandordirs; Name: "{app}\bibliotheque.db"
; Type: filesandordirs; Name: "{app}\recus"
; Type: filesandordirs; Name: "{app}\rapports"
; Type: filesandordirs; Name: "{app}\licence.key"

[Messages]
WelcomeLabel1=Bienvenue dans l'installation de{br}{#AppName}
WelcomeLabel2=Ce programme va installer {#AppName} version {#AppVersion} sur votre ordinateur.{br}{br}Développé par {#AppPublisher}{br}Contact : {#AppContact}{br}{br}Cliquez sur Suivant pour continuer.
