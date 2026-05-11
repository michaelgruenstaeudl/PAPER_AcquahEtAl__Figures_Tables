### Visualization of 16S rRNA metagenomic results across samples

#### Visualizing diversity at the taxonomic level of class
```bash
python stacked_taxonomy_bars.py . -r c -o HorseThief_metagenomics_rank-class -t 1 --metadata metadata_cyanobacteria_samples.tsv
```

#### Visualizing diversity at the taxonomic level of family but only for cyanobacteria
```bash
python stacked_taxonomy_bars.py . -r f -o HorseThief_metagenomics_rank-family_only_cyanos -t 1 --filter-rank c --filter-name Cyanobacteriia --metadata metadata_cyanobacteria_samples.tsv
```
