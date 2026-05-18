#!/bin/bash

# ----------------------------------------
# Count sequencing reads and infer average
# read size before and after quality
# filtering
# ----------------------------------------

OUTFILE="read_counts.txt"

{
echo "Read counts and average read sizes before and after quality filtering"
echo "====================================================================="
echo

# ----------------------------------------
# Illumina reads before filtering
# ----------------------------------------

echo "Illumina reads before filtering:"
echo -n "  R1: "
zcat Illumina_all_R1.fastq.gz | awk 'END {print NR / 4}'

echo -n "  R2: "
zcat Illumina_all_R2.fastq.gz | awk 'END {print NR / 4}'

echo

# ----------------------------------------
# Illumina reads after filtering
# ----------------------------------------

echo "Illumina reads after filtering:"
echo -n "  R1 paired (count): "
zcat Illumina_filt_R1_paired.fastq.gz | awk 'END {print NR / 4}'
echo -n "  R1 paired (avg read size, bp): "
zcat Illumina_filt_R1_paired.fastq.gz | awk 'NR % 4 == 2 {total += length($0); count++} END {printf "%.1f\n", (count > 0 ? total / count : 0)}'

echo -n "  R2 paired (count): "
zcat Illumina_filt_R2_paired.fastq.gz | awk 'END {print NR / 4}'
echo -n "  R2 paired (avg read size, bp): "
zcat Illumina_filt_R2_paired.fastq.gz | awk 'NR % 4 == 2 {total += length($0); count++} END {printf "%.1f\n", (count > 0 ? total / count : 0)}'

echo -n "  R1 unpaired (count): "
zcat Illumina_filt_R1_unpaired.fastq.gz | awk 'END {print NR / 4}'

echo -n "  R2 unpaired (count): "
zcat Illumina_filt_R2_unpaired.fastq.gz | awk 'END {print NR / 4}'

echo

# ----------------------------------------
# Nanopore reads before filtering
# ----------------------------------------

echo "Nanopore reads before filtering:"
echo -n "  All reads: "
zcat Nanopore_all.fastq.gz | awk 'END {print NR / 4}'

echo

# ----------------------------------------
# Nanopore reads after filtering
# ----------------------------------------

echo "Nanopore reads after filtering:"
echo -n "  Filtered reads (count): "
zcat Nanopore_filtered.q75.fastq.gz | awk 'END {print NR / 4}'
echo -n "  Filtered reads (avg read size, bp): "
zcat Nanopore_filtered.q75.fastq.gz | awk 'NR % 4 == 2 {total += length($0); count++} END {printf "%.1f\n", (count > 0 ? total / count : 0)}'

} > "$OUTFILE"

echo "Read counts written to: $OUTFILE"
