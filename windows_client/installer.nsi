; Maintenance Tracker Client Installer
; NSIS Script

!include "MUI2.nsh"

; Application information
!define APPNAME "Maintenance Tracker Client"
!define COMPANYNAME "AMRS"
!define DESCRIPTION "Client application for AMRS Preventative Maintenance System"
!define VERSIONMAJOR 1
!define VERSIONMINOR 0
!define VERSIONBUILD 0

; Installer attributes
!define INSTALLER_NAME "MaintenanceTrackerClient_Setup.exe"
!define INSTALL_DIR "$PROGRAMFILES64\${COMPANYNAME}\${APPNAME}"
!define REG_ROOT "HKLM"
!define REG_APP_PATH "Software\Microsoft\Windows\CurrentVersion\App Paths\MaintenanceTrackerClient.exe"
!define UNINSTALL_PATH "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"

; Set compression options
SetCompressor /SOLID lzma

Name "${APPNAME}"
Icon "app_icon.ico"
OutFile "${INSTALLER_NAME}"
InstallDir "${INSTALL_DIR}"
InstallDirRegKey ${REG_ROOT} "${REG_APP_PATH}" ""

; Request application privileges for Windows Vista and later
RequestExecutionLevel admin

; Modern UI configuration
!define MUI_ABORTWARNING
!define MUI_ICON "app_icon.ico"
!define MUI_UNICON "app_icon.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_RIGHT
!define MUI_HEADERIMAGE_BITMAP "installer_header.bmp"
!define MUI_WELCOMEFINISHPAGE_BITMAP "installer_welcome.bmp"
!define MUI_FINISHPAGE_RUN "$INSTDIR\MaintenanceTrackerClient.exe"
!define MUI_FINISHPAGE_NOAUTOCLOSE

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Language
!insertmacro MUI_LANGUAGE "English"

; Install sections
Section "MainSection" SEC01
    SetOutPath "$INSTDIR"
    
    ; Include all files from the dist directory
    File /r "dist\*.*"
    
    ; Create Start Menu shortcuts
    CreateDirectory "$SMPROGRAMS\${APPNAME}"
    CreateShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\MaintenanceTrackerClient.exe"
    CreateShortCut "$SMPROGRAMS\${APPNAME}\Uninstall.lnk" "$INSTDIR\uninstall.exe"
    
    ; Create desktop shortcut
    CreateShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\MaintenanceTrackerClient.exe"
    
    ; Write registry information for uninstaller
    WriteRegStr ${REG_ROOT} "${REG_APP_PATH}" "" "$INSTDIR\MaintenanceTrackerClient.exe"
    WriteRegStr ${REG_ROOT} "${UNINSTALL_PATH}" "DisplayName" "${APPNAME}"
    WriteRegStr ${REG_ROOT} "${UNINSTALL_PATH}" "DisplayIcon" "$INSTDIR\MaintenanceTrackerClient.exe"
    WriteRegStr ${REG_ROOT} "${UNINSTALL_PATH}" "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr ${REG_ROOT} "${UNINSTALL_PATH}" "DisplayVersion" "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}"
    WriteRegStr ${REG_ROOT} "${UNINSTALL_PATH}" "Publisher" "${COMPANYNAME}"
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

; Uninstall section
Section "Uninstall"
    ; Remove Start Menu shortcuts
    Delete "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk"
    Delete "$SMPROGRAMS\${APPNAME}\Uninstall.lnk"
    RMDir "$SMPROGRAMS\${APPNAME}"
    
    ; Remove desktop shortcut
    Delete "$DESKTOP\${APPNAME}.lnk"
    
    ; Remove files and directory
    Delete "$INSTDIR\*.*"
    RMDir /r "$INSTDIR"
    
    ; Remove registry keys
    DeleteRegKey ${REG_ROOT} "${REG_APP_PATH}"
    DeleteRegKey ${REG_ROOT} "${UNINSTALL_PATH}"
SectionEnd
