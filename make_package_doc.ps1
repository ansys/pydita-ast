#! /bin/sh

function Green
{
    process { Write-Host $_ -ForegroundColor Green }
}

deactivate
cd .\package\
uv venv .venv --seed
.\.venv\Scripts\activate
 Write-Output "A new virtual environment has been created within the package folder." | Green
uv pip install -e .[doc]
 Write-Output "The package has successfully been installed in the virtual environment." | Green
 Write-Output "The documentation is about to be built." | Green
.\doc\make.bat html
 Write-Output "The documentation has been successfully built." | Green
.\doc\_build\html\index.html
deactivate
cd ..