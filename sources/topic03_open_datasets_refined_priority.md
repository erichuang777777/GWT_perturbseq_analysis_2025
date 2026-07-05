# Topic 3 refined open dataset priority

Updated 2026-07-04. Purpose: executable download/integration priority for a GWT engine.

Top 10 priority:

1. Primary Human CD4+ T Cell Perturb-seq, CZI Virtual Cells. Large. URL: https://virtualcellmodels.cziscience.com/dataset/genome-scale-tcell-perturb-seq DOI: 10.64898/2025.12.23.696273v1. Use metadata/signatures first; avoid full download initially due to >22M cells.
2. GSE119450 CROP-seq in primary human T cells. Small/medium. URL: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE119450. Use full processed matrix if available.
3. GSE92872 Jurkat TCR CROP-seq. Small. URL: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE92872 PMID: 28099430. Download processed expression CSV.
4. Open Problems NeurIPS 2023 PBMC drug perturbation. Medium. URL: https://openproblems.bio/results/perturbation_prediction DOI: 10.1038/s41587-025-02694-w. Use benchmark files and signatures.
5. Sci-Plex3. Medium/large. URL: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE139944 and https://cellxgene.cziscience.com/collections/00109df5-7810-4542-8db5-2288c46e0424 PMID: 31806696 DOI: 10.1126/science.aax6234. Prefer h5ad subset or signatures first.
6. scPerturb resource. Medium. URL: https://projects.sanderlab.org/scperturb/ and https://plus.figshare.com/articles/dataset/scPerturb_Single-Cell_Perturbation_Data_RNA_and_protein_h5ad_files/24160713. Use selected h5ad datasets only.
7. PerturBase. Small if metadata/signatures only. URL: https://www.perturbase.cn/ PMID: 39377396. Use dataset/perturbation metadata and differential signatures first.
8. Perturb-CITE-seq melanoma/TIL SCP1064. Medium. URL: https://singlecell.broadinstitute.org/single_cell/study/SCP1064/multi-modal-pooled-perturb-cite-seq-screens-in-patient-models-define-novel-mechanisms-of-cancer-immune-evasion PMID: 33649592 DOI: 10.1038/s41588-021-00779-1. Use RNA/protein signatures for ICI/TME validation.
9. Disease atlases via CELLxGENE/SCP: UC SCP259, Crohn GSE134809, SLE GSE174188, RA AMP RA/SLE, psoriasis GSE162183. Small if disease-state signatures only; large if full h5ad.
10. Replogle genome-scale Perturb-seq. Large. URL: http://gwps.wi.mit.edu PRJNA831566 PMID: 35793669 DOI: 10.1016/j.cell.2022.05.013. Use pseudobulk/signatures first; do not full-download initially.

