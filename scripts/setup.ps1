[CmdletBinding()]
param (
    [Parameter()]
    [string]
    $python
)

$VERSION = '3.10'

function CheckPythonCommandVersion {
    param (
        [Parameter()]
        [string]
        $cmdName
    )
    try {
        $found = powershell $cmdName --version 2> $null
        return ($found -split '\n')[0].StartsWith("Python $VERSION.")
    }
    catch {
        return $false
    }
}

if ($python) {
    if (!(CheckPythonCommandVersion $python)) {
        Write-Output "'$python' is not a valid Python interpreter!"
        exit 1
    }
}
else {
    if (CheckPythonCommandVersion "py -3.10") {
        $python = "py"
    }
    elseif (CheckPythonCommandVersion python) {
        $python = "python"
    }
    elseif (CheckPythonCommandVersion python3) {
        $python = "python3"
    }
    else {
        Write-Output No valid Python interpreter found!
        exit 1
    }
}

powershell $python -m venv venv
.\venv\Scripts\Activate.ps1
powershell $python -m pip install --upgrade pip tox
pip install -e '.[dev]'
