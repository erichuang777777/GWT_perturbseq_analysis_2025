import { Suspense, lazy } from "react";
import Footer from "./components/Footer";
import Header from "./components/Header";
import { StoreProvider, useStore } from "./store/store";
import ApiDocs from "./views/ApiDocs";
import Clinical from "./views/Clinical";
import Compare from "./views/Compare";
import Dossier from "./views/Dossier";
import Explorer from "./views/Explorer";
import Deck from "./views/Deck";
import Docs from "./views/Docs";
import Home from "./views/Home";
import Provenance from "./views/Provenance";
import { InlineScreen } from "./components/ui/ScreenState";

// Figure atlas pulls in Plotly (~4 MB) — load it only when the atlas is opened.
const Figures = lazy(() => import("./views/Figures"));
const Gallery = lazy(() => import("./views/Gallery"));

function Router() {
  const { state } = useStore();
  switch (state.view) {
    case "home":
      return <Home />;
    case "explorer":
      return <Explorer />;
    case "dossier":
      return <Dossier />;
    case "compare":
      return <Compare />;
    case "clinical":
      return <Clinical />;
    case "figures":
      return (
        <Suspense fallback={<InlineScreen>Loading figure atlas…</InlineScreen>}>
          <Figures />
        </Suspense>
      );
    case "gallery":
      return (
        <Suspense fallback={<InlineScreen>Loading gallery…</InlineScreen>}>
          <Gallery />
        </Suspense>
      );
    case "apidocs":
      return <ApiDocs />;
    case "provenance":
      return <Provenance />;
    case "deck":
      return <Deck />;
    case "docs":
      return <Docs />;
    default:
      return <Home />;
  }
}

export default function App() {
  return (
    <StoreProvider>
      <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", background: "#ffffff" }}>
        <Header />
        <Router />
        <Footer />
      </div>
    </StoreProvider>
  );
}
