#!/bin/bash
# Calculate impact factors for major journals

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JOURNALS_FILE="$SCRIPT_DIR/major_journals.txt"
OUTPUT_DIR="$SCRIPT_DIR/results"
YEAR="${1:-2023}"

# Create output directory
mkdir -p "$OUTPUT_DIR"

OUTPUT_FILE="$OUTPUT_DIR/major_journals_IF_${YEAR}.csv"

echo "=================================="
echo "Calculating Impact Factors"
echo "=================================="
echo "Year: $YEAR"
echo "Journals file: $JOURNALS_FILE"
echo "Output: $OUTPUT_FILE"
echo ""
echo "This will take approximately 15-30 minutes for 30 journals"
echo "Press Ctrl+C to cancel"
echo ""
sleep 3

# Calculate IFs
cd "$SCRIPT_DIR/.."
python ./impact_factor/calculate_if.py \
    --journal-file "$JOURNALS_FILE" \
    --year "$YEAR" \
    --output "$OUTPUT_FILE" \
    --verbose

echo ""
echo "=================================="
echo "Complete!"
echo "=================================="
echo "Results saved to: $OUTPUT_FILE"
echo ""
echo "To view results:"
echo "  cat $OUTPUT_FILE"
echo "  column -t -s, $OUTPUT_FILE | less -S"
