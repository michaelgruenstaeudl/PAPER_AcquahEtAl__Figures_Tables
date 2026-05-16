### Assembly quality assessment

#### Table - Part 1: Extract read counts from sequence files
Foo bar baz

```bash
bash SCRIPT__get_read_counts.sh
```

#### Table - Part 2: Extract assembly stats from Unicycler log
Foo bar baz

```bash
DATDIR="DATA__Assembly_quality_assessment"

bash SCRIPT__extract_assembly_stats_from_Unicycler_log.sh ${DATDIR}/unicycler.log ${DATDIR}
```
