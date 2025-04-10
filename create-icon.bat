@echo off
echo Creating application icon...

REM Create icons directory if it doesn't exist
mkdir electron_app\icons 2>nul

REM Create a PowerShell script to generate the icon
echo $iconPath = "electron_app\icons\app.ico" > create_icon.ps1
echo $iconSize = New-Object System.Drawing.Size(256, 256) >> create_icon.ps1
echo $bmp = New-Object System.Drawing.Bitmap($iconSize.Width, $iconSize.Height) >> create_icon.ps1
echo $g = [System.Drawing.Graphics]::FromImage($bmp) >> create_icon.ps1
echo $g.Clear([System.Drawing.Color]::FromArgb(0x41, 0x69, 0xE1)) >> create_icon.ps1
echo $font = New-Object System.Drawing.Font("Arial", 100, [System.Drawing.FontStyle]::Bold) >> create_icon.ps1
echo $brush = [System.Drawing.Brushes]::White >> create_icon.ps1
echo $format = [System.Drawing.StringFormat]::GenericTypographic >> create_icon.ps1
echo $format.Alignment = [System.Drawing.StringAlignment]::Center >> create_icon.ps1
echo $format.LineAlignment = [System.Drawing.StringAlignment]::Center >> create_icon.ps1
echo $rect = New-Object System.Drawing.RectangleF(0, 0, $bmp.Width, $bmp.Height) >> create_icon.ps1
echo $g.DrawString("AM", $font, $brush, $rect, $format) >> create_icon.ps1
echo $g.Flush() >> create_icon.ps1
echo # Save as ICO file >> create_icon.ps1
echo $ico = New-Object System.Drawing.Icon([System.Drawing.Bitmap]$bmp, $iconSize) >> create_icon.ps1
echo $fs = New-Object System.IO.FileStream($iconPath, [System.IO.FileMode]::Create) >> create_icon.ps1
echo $ico.Save($fs) >> create_icon.ps1
echo $fs.Close() >> create_icon.ps1
echo $ico.Dispose() >> create_icon.ps1
echo $g.Dispose() >> create_icon.ps1
echo $bmp.Dispose() >> create_icon.ps1

REM Run the PowerShell script
powershell -ExecutionPolicy Bypass -File create_icon.ps1

REM Clean up the temporary script
del create_icon.ps1

echo Icon created at electron_app\icons\app.ico
echo You can now run: npm run dist
pause
