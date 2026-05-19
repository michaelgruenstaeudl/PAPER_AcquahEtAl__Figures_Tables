### Read statistics and assembly quality

#### Tables - Part 1: Extract read counts from sequence files
```bash
bash SCRIPT__get_read_counts.sh
```

#### Tables - Part 2: Extract assembly stats from Unicycler log
```bash
DATDIR="DATA__Assembly_quality_assessment"

bash SCRIPT__extract_assembly_stats_from_Unicycler_log.sh ${DATDIR}/unicycler.log ${DATDIR}
```

#### Tables - Part 3: Extract mapping stats for short-read sequence data
```bash
cd <Bactopia output directory>
bash SCRIPT__short_read_alignment_summarizer.sh
```
