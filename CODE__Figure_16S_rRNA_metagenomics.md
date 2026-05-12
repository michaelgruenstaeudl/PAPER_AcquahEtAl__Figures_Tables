### Visualization of 16S rRNA metagenomic results across samples
```bash
DATDIR="DATA__Figure_16S_rRNA_metagenomics"
OUTDIR="VIZ__Figure_16S_rRNA_metagenomics"
```

#### Visualizing diversity at the taxonomic level of class
```bash
python SCRIPT__stacked_taxonomy_bars.py \
    $DATDIR/ \
    -r c \
    -o $OUTDIR/Fig_16S_rRNA_metagenomics_rank-class \
    -t 1 \
    --metadata $DATDIR/metadata_cyanobacteria_samples.tsv

```

#### Visualizing diversity at the taxonomic level of family but only for cyanobacteria
```bash
python SCRIPT__stacked_taxonomy_bars.py \
    $DATDIR/ \
    -r c \
    -o $OUTDIR/Fig_16S_rRNA_metagenomics \
    -t 1 \
    --metadata $DATDIR/metadata_cyanobacteria_samples.tsv

python stacked_taxonomy_bars.py . -r f -o HorseThief_metagenomics_rank-family_only_cyanos -t 1 --filter-rank c --filter-name Cyanobacteriia --metadata metadata_cyanobacteria_samples.tsv
```
