# Structure Visualization Assets — Perturbase (50 signed-top genes)

Grounded structure-visualization asset set for 3D display and 2D topology panels.
Every diagram is derived from **reviewed human UniProt** annotation and **InterPro**
domain architecture; no structures or topologies are invented.

## Contents
- `cif/AF-<ACCESSION>-F1-model_v6.cif` — AlphaFold predicted structures (48 of 50 genes)
- `protter/protter_<GENE>_<ACCESSION>.png` — Protter-style topology diagrams (50 of 50, 300 dpi)
- `structures_index.csv` — one row per gene (join key for the website)

## Provenance
| Source | Use |
|--------|-----|
| UniProtKB REST (reviewed, organism 9606) | accession, sequence length, signal peptide, transmembrane, topological domains |
| InterPro (`get_domain_architecture`) | domain / repeat blocks with residue ranges |
| AlphaFold DB (EBI), model v6 | 3D predicted structure (.cif) + global pLDDT |

## Genes without an AlphaFold model
Two genes exceed the AlphaFold DB single-chain length limit and have **no** deposited model:
- **MGA** (Q8IWI9, 3065 aa)
- **VPS13A** (Q96RL7, 3174 aa)

For these, the 3D panel should show a "structure not available in AlphaFold DB" placeholder.
Their Protter topology PNG is still provided (domain architecture from InterPro).

## Website embedding

### 3D structure (Mol*)
Serve each `.cif` and load into a Mol* viewer. Color by pLDDT (AlphaFold confidence)
using the per-residue B-factor column, which AlphaFold populates with pLDDT (0-100):
```
very high  pLDDT > 90   #0053D6
confident  70-90        #65CBF3
low        50-70        #FFDB13
very low   < 50         #FF7D45
```
Row `has_alphafold == False` -> render the placeholder instead of a viewer.

### 2D topology (Protter panel)
Embed `protter/protter_<GENE>_<ACCESSION>.png` directly as the topology panel image.
Panel conventions:
- **Transmembrane proteins** (10): red rounded helices span a tan membrane band;
  backbone loops alternate between the extracellular/lumenal side (top) and cytoplasmic
  side (bottom), placed from UniProt topological-domain sidedness. N/C termini marked.
  Signal peptides drawn as an orange bar on the N-terminal loop.
  TM genes: TMEM131L, ERN1, TMEM205, IFNGR2, TMEM131, NCR3, CDIPT, GPAA1, XBP1, ATP1B3
- **Soluble proteins** (no predicted TM): horizontal backbone with colored InterPro domain
  blocks and residue-grounded labels; header notes "no predicted TM; domain architecture shown".
  Repeated identical domains are merged into one block labeled "N x <domain>".
- Two soluble genes (**LIN37**, **TENT5C**) have no InterPro domain resolved over the
  modeled region; their panel carries a "family-level annotation only" note and shows the bare backbone.

## structures_index.csv columns
`gene, uniprot, protein_name, plddt, length, n_domains, n_tm, n_signal, topology_class,
cif_filename, has_alphafold, alphafold_note, protter_filename`

- `plddt` — AlphaFold global pLDDT (blank if no model)
- `n_domains` — InterPro domain/repeat blocks used in the Protter diagram
- `n_tm` / `n_signal` — UniProt transmembrane / signal-peptide feature counts
- `topology_class` — `transmembrane` or `soluble`
- `cif_filename` — basename under `cif/` (blank if no AlphaFold model)
- `protter_filename` — basename under `protter/`

## Summary
- Genes resolved to reviewed human UniProt: **50 / 50**
- AlphaFold structures downloaded: **48 / 50** (MGA, VPS13A unavailable)
- Protter topology diagrams: **50 / 50**
- Transmembrane proteins: **10**  ·  Soluble: **40**
