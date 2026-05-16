#!/bin/bash

set -euo pipefail

ASSEMBLY_GZ="output/work/df/655e18ffe851e4c2245bc5e00a9562/results/Limnothrix_Unicycler.fna.gz"
ASSEMBLY="Limnothrix_Unicycler.fna"

R1="input/Illumina_filt_R1_paired.fastq.gz"
R2="input/Illumina_filt_R2_paired.fastq.gz"

OUT="short_read_alignment_summary.txt"
BAM="short_reads_on_assembly.bam"
READ_LENGTH_BP=150
FLAGSTAT_FILE="short_reads_on_assembly.flagstat.txt"
IDXSTATS_FILE="short_reads_on_assembly.idxstats.txt"

cleanup_generated_files() {
    rm -f "$ASSEMBLY"
    rm -f "${ASSEMBLY}.amb" "${ASSEMBLY}.ann" "${ASSEMBLY}.bwt" "${ASSEMBLY}.pac" "${ASSEMBLY}.sa"
    rm -f "$BAM" "${BAM}.bai"
    rm -f "$FLAGSTAT_FILE" "$IDXSTATS_FILE"
}

trap cleanup_generated_files EXIT

# Decompress assembly FASTA
gunzip -c "$ASSEMBLY_GZ" > "$ASSEMBLY"

# Index assembly
bwa index "$ASSEMBLY"

# Align reads and sort BAM
bwa mem -t 8 "$ASSEMBLY" "$R1" "$R2" | \
    samtools sort -@ 8 -o "$BAM"

# Index BAM
samtools index "$BAM"

# Collect raw metrics once so they can be printed and parsed consistently
samtools flagstat "$BAM" > "$FLAGSTAT_FILE"
samtools idxstats "$BAM" > "$IDXSTATS_FILE"

# Parse key values from flagstat
read -r TOTAL_READS MAPPED_READS MAPPED_PCT PROPERLY_PAIRED PROPERLY_PAIRED_PCT DUPLICATES SINGLETONS SINGLETON_PCT CROSS_CONTIG CROSS_CONTIG_MAPQ5 <<EOF
$(awk '
BEGIN {
    total="0"; mapped="0"; mapped_pct="0.00"; properly_paired="0"; properly_paired_pct="0.00"
    duplicates="0"; singletons="0"; singleton_pct="0.00"; cross_contig="0"; cross_contig_mapq5="0"
}
/ in total / {
    total=$1
}
/ mapped \(/ && $0 !~ /primary mapped/ {
    mapped=$1
    if (match($0, /\(([0-9.]+)%/, m)) {
        mapped_pct=m[1]
    }
}
/ properly paired / {
    properly_paired=$1
    if (match($0, /\(([0-9.]+)%/, m)) {
        properly_paired_pct=m[1]
    }
}
/ duplicates / {
    duplicates=$1
}
/ singletons / {
    singletons=$1
    if (match($0, /\(([0-9.]+)%/, m)) {
        singleton_pct=m[1]
    }
}
/with mate mapped to a different chr \(mapQ>=5\)/ {
    cross_contig_mapq5=$1
}
/with mate mapped to a different chr$/ {
    cross_contig=$1
}
END {
    print total, mapped, mapped_pct, properly_paired, properly_paired_pct, duplicates, singletons, singleton_pct, cross_contig, cross_contig_mapq5
}
' "$FLAGSTAT_FILE")
EOF

# Parse contig-level metrics and estimate per-contig coverage
MAIN_CONTIG=$(awk '$1 != "*" { if ($3 > max_reads) { max_reads=$3; name=$1 } } END { print name }' "$IDXSTATS_FILE")
MAIN_CONTIG_LEN=$(awk -v c="$MAIN_CONTIG" '$1 == c { print $2 }' "$IDXSTATS_FILE")
MAIN_CONTIG_MAPPED=$(awk -v c="$MAIN_CONTIG" '$1 == c { print $3 }' "$IDXSTATS_FILE")
TOTAL_MAPPED_FROM_IDXSTATS=$(awk '$1 != "*" { sum += $3 } END { print sum+0 }' "$IDXSTATS_FILE")
UNMAPPED_READS=$(awk '$1 == "*" { print $4 }' "$IDXSTATS_FILE")

if [ "$MAIN_CONTIG_LEN" -gt 0 ]; then
    MAIN_CONTIG_COV=$(awk -v m="$MAIN_CONTIG_MAPPED" -v l="$MAIN_CONTIG_LEN" -v rl="$READ_LENGTH_BP" 'BEGIN { printf "%.2f", (m * rl) / l }')
else
    MAIN_CONTIG_COV="0.00"
fi

UNMAPPED_PCT=$(awk -v m="$TOTAL_MAPPED_FROM_IDXSTATS" -v u="$UNMAPPED_READS" 'BEGIN { t=m+u; if (t>0) printf "%.2f", (u*100)/t; else print "0.00" }')

# Write summary report
{
echo "Short-read alignment summary"
echo "============================"
echo

cat "$FLAGSTAT_FILE"

echo
echo "Per-contig mapping summary"
echo "=========================="
echo

cat "$IDXSTATS_FILE"

echo
echo "Interpretation"
echo "=============="
echo
echo "Key observations"
echo "- ${MAPPED_READS} mapped (${MAPPED_PCT}%): nearly all Illumina reads map back to the assembly."
echo "- ${PROPERLY_PAIRED} properly paired (${PROPERLY_PAIRED_PCT}%): pairing and orientation are highly consistent with the assembly structure."
echo "- ${DUPLICATES} duplicates: duplicate marking is not present or no duplicates were reported in this BAM."
echo "- ${SINGLETONS} singletons (${SINGLETON_PCT}%): very few discordant pair mappings."
echo "- ${CROSS_CONTIG} reads with mate on a different contig (${CROSS_CONTIG_MAPQ5} at mapQ>=5): low structural ambiguity signal."
echo
echo "Main contig"
echo "- Primary contig by mapped read support: ${MAIN_CONTIG}"
echo "- Length: ${MAIN_CONTIG_LEN} bp"
echo "- Mapped reads: ${MAIN_CONTIG_MAPPED}"
echo "- Approximate coverage (assuming ${READ_LENGTH_BP} bp reads): ${MAIN_CONTIG_COV}x"
echo
echo "Unmapped reads"
echo "- Unmapped reads: ${UNMAPPED_READS} (${UNMAPPED_PCT}% of mapped+unmapped in idxstats)."
echo "- A small unmapped fraction is expected and can reflect residual adapters, low-quality bases, contamination, repetitive regions, or sequence heterogeneity."
echo
echo "Overall interpretation"
echo "- This assembly is strongly supported when mapped and properly paired rates are high and cross-contig mate counts remain low."
echo "- Large coverage differences between contigs in the table often indicate plasmids, repeats, or copy-number variation."

} > "$OUT"

echo "Short-read alignment summary written to: $OUT"
