### Visualization of 16S rRNA metagenomic results across samples

#### Genetic diversity
This script visualizes the metagenomic diversity across different samples at different taxonomic levels.

```bash
DATDIR="DATA__Figure_16S_rRNA_metagenomics"
OUTDIR="VIZ__Figure_16S_rRNA_metagenomics"

python SCRIPT__vertically_stacked_taxonomy_barcharts.py \
    $DATDIR/ \
    -r c \
    -o $OUTDIR/Fig_16S_rRNA_metagenomics \
    -t 1 \
    --metadata $DATDIR/metadata__genus-table.csv
```

#### Diversity indices
This script visualizes the diversity indices across different samples.

```bash
DATDIR="DATA__Figure_16S_rRNA_metagenomics"
OUTDIR="VIZ__Figure_16S_rRNA_metagenomics"

python SCRIPT__horizontally_stacked_diversity_index_barcharts.py \
    $DATDIR/ \
    -o $OUTDIR/Fig_16S_rRNA_diversityIndices \
    --metadata $DATDIR/metadata__METRICS.csv
```
