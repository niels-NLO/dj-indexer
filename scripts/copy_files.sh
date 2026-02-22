#!/bin/bash

#
# Copy or move files listed in a CSV to a destination directory
#
# Usage:
#   ./copy_files.sh -c results.csv -d /path/to/destination
#   ./copy_files.sh -c results.csv -d /path/to/destination -m move
#   ./copy_files.sh -c results.csv -d /path/to/destination --subfolder --skip-exists
#

# Default values
filepath_column="filepath"
mode="copy"
create_subfolder=false
skip_if_exists=false

# Help message
show_help() {
    cat << EOF
Copy or move files from CSV export to a destination directory

Usage: $0 -c CSV_FILE -d DESTINATION [OPTIONS]

Required arguments:
  -c, --csv FILE              CSV file exported from dj-indexer
  -d, --destination PATH      Destination directory

Optional arguments:
  -m, --mode MODE             'copy' (default) or 'move'
  --column COLUMN             CSV column with filepaths (default: 'filepath')
  --subfolder                 Recreate source folder structure
  --skip-exists               Skip files that already exist in destination
  -v, --verbose               Show detailed output
  -h, --help                  Show this help message

Examples:
  ./copy_files.sh -c results.csv -d ~/Music/Staging
  ./copy_files.sh -c results.csv -d ~/Music/Backup -m move
  ./copy_files.sh -c techno.csv -d ~/DJ/Prep --subfolder

EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--csv)
            csv_file="$2"
            shift 2
            ;;
        -d|--destination)
            destination="$2"
            shift 2
            ;;
        -m|--mode)
            mode="$2"
            shift 2
            ;;
        --column)
            filepath_column="$2"
            shift 2
            ;;
        --subfolder)
            create_subfolder=true
            shift
            ;;
        --skip-exists)
            skip_if_exists=true
            shift
            ;;
        -v|--verbose)
            verbose=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Validate required arguments
if [[ -z "$csv_file" ]] || [[ -z "$destination" ]]; then
    echo "Error: CSV file and destination are required"
    show_help
    exit 1
fi

# Check CSV exists
if [[ ! -f "$csv_file" ]]; then
    echo "Error: CSV file not found: $csv_file"
    exit 1
fi

# Create destination if needed
if [[ ! -d "$destination" ]]; then
    echo "Creating destination directory: $destination"
    mkdir -p "$destination"
fi

# Validate mode
if [[ "$mode" != "copy" ]] && [[ "$mode" != "move" ]]; then
    echo "Error: Mode must be 'copy' or 'move'"
    exit 1
fi

# Statistics
total=0
success=0
failed=0
skipped=0
not_found=0

# Get column index from header
read -r header < "$csv_file"
IFS=',' read -ra columns <<< "$header"
col_index=-1

for i in "${!columns[@]}"; do
    # Trim whitespace from column name
    col="${columns[$i]//[[:space:]]/}"
    if [[ "$col" == "$filepath_column" ]]; then
        col_index=$i
        break
    fi
done

if [[ $col_index -lt 0 ]]; then
    echo "Error: Column '$filepath_column' not found in CSV"
    echo "Available columns: ${columns[@]}"
    exit 1
fi

# Process each row (skip header)
tail -n +2 "$csv_file" | while IFS=',' read -ra row; do
    ((total++))

    # Extract filepath (handle quoted fields)
    source_file="${row[$col_index]}"
    source_file="${source_file//\"/}"  # Remove quotes
    source_file="${source_file//[[:space:]]/}"  # Trim whitespace

    # Skip empty paths
    if [[ -z "$source_file" ]]; then
        echo "[$total] Skipped: Empty filepath"
        ((skipped++))
        continue
    fi

    # Expand tilde if present
    source_file="${source_file/#\~/$HOME}"

    # Check if file exists
    if [[ ! -f "$source_file" ]]; then
        echo "[$total] Not found: $source_file"
        ((not_found++))
        continue
    fi

    # Get filename
    filename=$(basename "$source_file")
    dest_dir="$destination"

    # Recreate subfolder structure if requested
    if [[ "$create_subfolder" == true ]]; then
        source_dir=$(dirname "$source_file")
        subfolder=$(basename "$source_dir")
        dest_dir="$destination/$subfolder"
        mkdir -p "$dest_dir"
    fi

    dest_file="$dest_dir/$filename"

    # Check if destination exists
    if [[ -f "$dest_file" ]] && [[ "$skip_if_exists" == true ]]; then
        echo "[$total] Skipped (exists): $filename"
        ((skipped++))
        continue
    fi

    # Copy or move
    if [[ "$mode" == "copy" ]]; then
        if cp "$source_file" "$dest_file" 2>/dev/null; then
            echo "[$total] Copied: $filename"
            ((success++))
        else
            echo "[$total] Failed to copy: $filename"
            ((failed++))
        fi
    else
        if mv "$source_file" "$dest_file" 2>/dev/null; then
            echo "[$total] Moved: $filename"
            ((success++))
        else
            echo "[$total] Failed to move: $filename"
            ((failed++))
        fi
    fi
done

# Print summary
echo ""
echo "========================================"
echo "Operation Complete"
echo "========================================"
echo "Total processed:  $total"
echo "Successful:       $success"
echo "Failed:           $failed"
echo "Skipped:          $skipped"
echo "Not found:        $not_found"
echo "========================================"
echo ""

if [[ $failed -gt 0 ]]; then
    exit 1
fi
