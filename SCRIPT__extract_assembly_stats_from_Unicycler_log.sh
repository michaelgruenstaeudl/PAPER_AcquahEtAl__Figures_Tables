#!/bin/bash

# ----------------------------------------
# Extract key assembly statistics from
# a Unicycler log file
#
# Usage:
#   ./SCRIPT__extract_assembly_stats_from_Unicycler_log.sh unicycler.log [output_path]
# ----------------------------------------

# Check input
if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    echo "Usage: $0 <unicycler.log> [output_path]"
    exit 1
fi

LOGFILE="$1"

# Check file existence
if [ ! -f "$LOGFILE" ]; then
    echo "Error: File not found: $LOGFILE"
    exit 1
fi

# Define output file
BASENAME=$(basename "$LOGFILE")

if [ -n "$2" ]; then
    if [ -d "$2" ]; then
        OUTFILE="$2/${BASENAME%.log}_summary.txt"
    else
        OUTFILE="$2"
    fi
else
    OUTFILE="${BASENAME%.log}_summary.txt"
fi

{
awk '
/Bridged assembly graph/ {
    print
    flag=1
}
flag && /Component/ {
    print
    getline; print
    getline; print
    getline; print
    getline; print
    flag=0
}
' "$LOGFILE"

echo

awk '
/Read alignment summary/ {
    print
    flag=1
}
flag && /Total read count:/ {print}
flag && /Fully aligned reads:/ {print}
flag && /Partially aligned reads:/ {print}
flag && /Unaligned reads:/ {print}
flag && /Total bases aligned:/ {print}
flag && /Mean alignment identity:/ {
    print
    flag=0
}
' "$LOGFILE"

echo

awk '
/^K-mer[[:space:]]+Contigs[[:space:]]+Dead ends[[:space:]]+Score/ {
    print
    flag=1
    next
}
flag && /^$/ {
    flag=0
    next
}
flag {
    print
}
' "$LOGFILE"

echo

grep "Read depth filter:" "$LOGFILE"

echo

awk '
/Merging segments into unitigs:/ {
    print
    flag=1
}
flag && /circular unitig/ {print}
flag && /linear unitigs/ {print}
flag && /total size/ {
    print
    flag=0
}
' "$LOGFILE"

echo

grep "Saving .*assembly.gfa" "$LOGFILE"
grep "Saving .*assembly.fasta" "$LOGFILE"

} > "$OUTFILE"

echo "Summary written to: $OUTFILE"
