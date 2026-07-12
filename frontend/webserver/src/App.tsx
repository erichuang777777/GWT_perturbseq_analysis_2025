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
import Home from "./views/Home";
import Provenance from "./views/Provenance";

// Figure atlas pulls in Plotly (~4 MB) — load it only when the atlas is opened.
const Figures = lazy(() => import("./views/Figures"));

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
        <Suspense
          fallback={
            <main style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "#9aa1ad", fontSize: "14px" }}>
              Loading figure atlas…
            </main>
          }
        >
          <Figures />
        </Suspense>
      );
    case "apidocs":
      return <ApiDocs />;
    case "provenance":
      return <Provenance />;
    case "deck":
      return <Deck />;
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
