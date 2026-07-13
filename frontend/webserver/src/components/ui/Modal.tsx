import { useEffect } from "react";

// Full-screen dismissable overlay + centered card chrome (Esc to close,
// backdrop click to close, body-scroll lock). Originally written for the
// Gallery figure/structure lightboxes; generalized so any future detail
// view (e.g. a disease-dossier reader) can reuse it instead of re-deriving
// the same overlay mechanics.
export default function Modal({ children, onClose, maxWidth = "760px" }: { children: React.ReactNode; onClose: () => void; maxWidth?: string }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [onClose]);

  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 100,
        background: "rgba(20,22,28,.55)",
        backdropFilter: "blur(3px)",
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "center",
        padding: "40px 20px",
        overflowY: "auto",
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          position: "relative",
          width: "100%",
          maxWidth,
          background: "#fff",
          borderRadius: "16px",
          padding: "26px 28px 30px",
          boxShadow: "0 24px 60px -12px rgba(20,22,28,.4)",
        }}
      >
        <button
          onClick={onClose}
          aria-label="Close"
          style={{
            position: "absolute",
            top: "16px",
            right: "16px",
            width: "30px",
            height: "30px",
            border: "none",
            borderRadius: "8px",
            background: "#f2f3f6",
            color: "#5b6270",
            fontSize: "17px",
            cursor: "pointer",
            lineHeight: 1,
          }}
        >
          ×
        </button>
        {children}
      </div>
    </div>
  );
}
