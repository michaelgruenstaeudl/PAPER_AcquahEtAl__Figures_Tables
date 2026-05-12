### Visualization of 16S rRNA metagenomic results across samples
This script visualizes the metagenomic diversity across different samples at different taxonomic levels.

```bash
DATDIR="DATA__Figure_16S_rRNA_metagenomics"
OUTDIR="VIZ__Figure_16S_rRNA_metagenomics"

python SCRIPT__stacked_taxonomy_bars.py \
    $DATDIR/ \
    -r c \
    -o $OUTDIR/Fig_16S_rRNA_metagenomics \
    -t 1 \
    --metadata $DATDIR/metadata_cyanobacteria_samples.csv
```


