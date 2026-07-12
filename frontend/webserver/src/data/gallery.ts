// Runtime loader for the curated figure & structure gallery. The assets and
// their bilingual, provenance-stamped metadata live in public/gallery/ (71
// rendered figures + 50 AlphaFold/Protter protein structures). We fetch the
// two small JSON catalogs lazily when the Gallery view first mounts, so they
// never bloat the initial app load. Images are served on demand by the CDN.

export interface ChartLang {
  title: string;
  family: string;
  description: string;
  data_explanation: string;
}

export interface GalleryChart {
  id: string;
  group: string;
  img: string;
  en: ChartLang;
  zh: ChartLang;
  raw_source: string;
}

export interface GalleryStructure {
  gene: string;
  uniprot: string;
  protein_name: string;
  plddt: number | null;
  length: number | null;
  n_domains: number | null;
  n_tm: number | null;
  topology_class: string;
  cif: string | null;
  protter: string | null;
  has_alphafold: boolean;
  note: string;
}

export interface GalleryData {
  charts: GalleryChart[];
  structures: GalleryStructure[];
}

// Prefix a gallery-relative path (e.g. "figures/C1.png") with the app base URL
// so it resolves both at the site root and under a sub-path deploy.
export const galleryAsset = (rel: string) =>
  `${import.meta.env.BASE_URL}gallery/${rel}`;

let cache: GalleryData | null = null;
let inflight: Promise<GalleryData> | null = null;

export function loadGallery(): Promise<GalleryData> {
  if (cache) return Promise.resolve(cache);
  if (inflight) return inflight;
  const base = `${import.meta.env.BASE_URL}gallery/data/`;
  inflight = Promise.all([
    fetch(`${base}charts.json`).then((r) => {
      if (!r.ok) throw new Error(`charts.json ${r.status}`);
      return r.json();
    }),
    fetch(`${base}structures.json`).then((r) => {
      if (!r.ok) throw new Error(`structures.json ${r.status}`);
      return r.json();
    }),
  ]).then(([charts, structures]) => {
    cache = {
      charts: charts as GalleryChart[],
      structures: structures as GalleryStructure[],
    };
    return cache;
  });
  return inflight;
}
