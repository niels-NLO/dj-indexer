#requires -version 3.0

<#
.SYNOPSIS
Copy or move files listed in a CSV to a destination directory.

.DESCRIPTION
Reads a CSV file with a 'filepath' column and copies or moves all files
to a specified destination. Useful for batch operations on search/query results.

.PARAMETER CsvFile
Path to the CSV file exported from dj-indexer

.PARAMETER DestinationPath
Destination directory where files will be copied/moved

.PARAMETER FilepathColumn
Name of the column containing file paths (default: 'filepath')

.PARAMETER Mode
'copy' to copy files, 'move' to move files (default: 'copy')

.PARAMETER CreateSubfolders
If true, recreates the source folder structure in destination

.PARAMETER SkipIfExists
If true, skip files that already exist in destination

.EXAMPLE
.\copy_files.ps1 -CsvFile results.csv -DestinationPath "C:\Staging"

.EXAMPLE
.\copy_files.ps1 -CsvFile results.csv -DestinationPath "D:\Backup" -Mode move -CreateSubfolders

.EXAMPLE
.\copy_files.ps1 -CsvFile techno_tracks.csv -DestinationPath "E:\Prep" -Mode copy -SkipIfExists
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$CsvFile,

    [Parameter(Mandatory = $true)]
    [string]$DestinationPath,

    [string]$FilepathColumn = 'filepath',

    [ValidateSet('copy', 'move')]
    [string]$Mode = 'copy',

    [switch]$CreateSubfolders,

    [switch]$SkipIfExists,

    [switch]$Verbose
)

# Validate inputs
if (-not (Test-Path $CsvFile)) {
    Write-Error "CSV file not found: $CsvFile"
    exit 1
}

if (-not (Test-Path $DestinationPath)) {
    Write-Host "Creating destination directory: $DestinationPath"
    New-Item -ItemType Directory -Path $DestinationPath -Force | Out-Null
}

# Import CSV
try {
    $data = Import-Csv -Path $CsvFile
    Write-Host "Loaded $($data.Count) records from CSV"
}
catch {
    Write-Error "Failed to read CSV: $_"
    exit 1
}

# Check if filepath column exists
if ($data.Count -gt 0) {
    if (-not ($data[0].PSObject.Properties.Name -contains $FilepathColumn)) {
        Write-Error "Column '$FilepathColumn' not found in CSV"
        Write-Host "Available columns: $($data[0].PSObject.Properties.Name -join ', ')"
        exit 1
    }
}

# Statistics
$stats = @{
    Total       = 0
    Success     = 0
    Failed      = 0
    Skipped     = 0
    NotFound    = 0
}

# Process each file
foreach ($row in $data) {
    $sourceFile = $row.$FilepathColumn
    $stats.Total++

    # Skip empty paths
    if ([string]::IsNullOrWhiteSpace($sourceFile)) {
        Write-Warning "[$($stats.Total)] Empty filepath"
        $stats.Skipped++
        continue
    }

    # Check if source exists
    if (-not (Test-Path $sourceFile)) {
        Write-Warning "[$($stats.Total)] File not found: $sourceFile"
        $stats.NotFound++
        continue
    }

    try {
        $file = Get-Item -Path $sourceFile
        $destFullPath = $DestinationPath

        # Recreate subfolder structure if requested
        if ($CreateSubfolders) {
            $relativePath = Split-Path -Path $sourceFile
            $subfolder = Split-Path -Path $relativePath -Leaf
            $destFullPath = Join-Path -Path $DestinationPath -ChildPath $subfolder

            if (-not (Test-Path $destFullPath)) {
                New-Item -ItemType Directory -Path $destFullPath -Force | Out-Null
            }
        }

        $destFile = Join-Path -Path $destFullPath -ChildPath $file.Name

        # Check if destination file exists
        if ((Test-Path $destFile) -and $SkipIfExists) {
            Write-Host "[$($stats.Total)] Skipped (exists): $($file.Name)"
            $stats.Skipped++
            continue
        }

        # Copy or move
        if ($Mode -eq 'copy') {
            Copy-Item -Path $sourceFile -Destination $destFile -Force
            Write-Host "[$($stats.Total)] Copied: $($file.Name)"
        }
        else {
            Move-Item -Path $sourceFile -Destination $destFile -Force
            Write-Host "[$($stats.Total)] Moved: $($file.Name)"
        }

        $stats.Success++
    }
    catch {
        Write-Host "[$($stats.Total)] Error: $_"
        $stats.Failed++
    }
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Operation Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Total processed:  $($stats.Total)"
Write-Host "Successful:       $($stats.Success)" -ForegroundColor Green
Write-Host "Failed:           $($stats.Failed)" -ForegroundColor Red
Write-Host "Skipped:          $($stats.Skipped)"
Write-Host "Not found:        $($stats.NotFound)" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($stats.Failed -gt 0) {
    exit 1
}
