#!/bin/bash
# Calculate impact factors for major journals in parallel

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JOURNALS_FILE="$SCRIPT_DIR/major_journals.txt"
OUTPUT_DIR="$SCRIPT_DIR/results"
YEAR="${1:-2023}"
PARALLEL_JOBS="${2:-4}"  # Number of parallel jobs

# Create output directory
mkdir -p "$OUTPUT_DIR"
TEMP_DIR="$OUTPUT_DIR/temp_$$"
mkdir -p "$TEMP_DIR"

echo "=================================="
echo "Calculating Impact Factors (Parallel)"
echo "=================================="
echo "Year: $YEAR"
echo "Parallel jobs: $PARALLEL_JOBS"
echo "Journals file: $JOURNALS_FILE"
echo ""

# Function to calculate IF for a single journal
calculate_if() {
    local journal="$1"
    local year="$2"
    local output_file="$3"

    cd "$SCRIPT_DIR/.."
    python ./impact_factor/calculate_if.py \
        --journal "$journal" \
        --year "$year" \
        --output "$output_file" \
        2>&1 | sed "s/^/[$journal] /"
}

export -f calculate_if
export SCRIPT_DIR
export YEAR

# Process journals in parallel
cat "$JOURNALS_FILE" | \
    parallel -j "$PARALLEL_JOBS" \
    "calculate_if '{}' $YEAR '$TEMP_DIR/{#}.csv'"

# Combine results
OUTPUT_FILE="$OUTPUT_DIR/major_journals_IF_${YEAR}.csv"
echo "journal,target_year,window_years,window_range,total_articles,total_citations,impact_factor,moving_average,method,status" > "$OUTPUT_FILE"

# Merge all temp files (skip headers)
for f in "$TEMP_DIR"/*.csv; do
    if [ -f "$f" ]; then
        tail -n +2 "$f" >> "$OUTPUT_FILE"
    fi
done

# Clean up temp files
rm -rf "$TEMP_DIR"

echo ""
echo "=================================="
echo "Complete!"
echo "=================================="
echo "Results saved to: $OUTPUT_FILE"
echo ""
echo "To view results sorted by IF:"
echo "  (head -n 1 $OUTPUT_FILE && tail -n +2 $OUTPUT_FILE | sort -t, -k7 -nr) | column -t -s,"
