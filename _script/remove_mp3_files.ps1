# Define the base directory
$baseDir = "C:\Path\To\Your\Directory"

# Get all *.mp3 files in subdirectories
$mp3Files = Get-ChildItem -Path $baseDir -Recurse -Filter *.mp3

# Loop through each file and remove it
foreach ($file in $mp3Files) {
    try {
        Remove-Item -Path $file.FullName -Force
        Write-Output "Deleted: $($file.FullName)"
    } catch {
        Write-Error "Failed to delete: $($file.FullName). Error: $_"
    }
}
