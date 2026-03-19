import { useRef, useState, useEffect, useCallback } from "react";
import { pollDocumentStatus } from "../services/documentApi";
import UploadStatusBanner from "./UploadStatusBanner";

function UploadPanel({ onSubmit }) {
  const fileInputRef = useRef(null);
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [polling, setPolling] = useState(null);

  const stopPolling = useCallback(() => {
    setPolling(null);
  }, []);

  useEffect(() => {
    if (!polling) return;

    const interval = setInterval(async () => {
      try {
        const result = await pollDocumentStatus(polling.dagRunId);
        if (result.state === "success") {
          setSuccess(`Document "${polling.fileName}" traité avec succès.`);
          stopPolling();
        } else if (result.state === "failed") {
          setError(`Le traitement de "${polling.fileName}" a échoué.`);
          setSuccess("");
          stopPolling();
        }
      } catch {
        // keep polling
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [polling, stopPolling]);

  const handleUpload = async (file) => {
    if (!file) return;
    setSuccess("");
    setError("");
    setLoading(true);

    try {
      const created = await onSubmit({ file });
      setSuccess(`Document "${created.fileName}" déposé avec succès. Analyse en cours...`);
      if (created.dagRunId) {
        setPolling({ dagRunId: created.dagRunId, fileName: created.fileName });
      }
    } catch {
      setError("Echec de l'envoi du document.");
    }

    setLoading(false);
  };

  const handleFileChange = (event) => {
    const file = event.target.files && event.target.files[0];
    handleUpload(file);
    event.target.value = "";
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setIsDragging(false);
    const file = event.dataTransfer.files && event.dataTransfer.files[0];
    handleUpload(file);
  };

  const openFilePicker = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  return (
    <section className="upload-panel">
      <div
        className={isDragging ? "drop-zone dragging" : "drop-zone"}
        onClick={() => {
          if (!loading) {
            openFilePicker();
          }
        }}
        onDragOver={(event) => {
          if (loading) return;
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        role="button"
        tabIndex={0}
        onKeyDown={(event) => {
          if (loading) return;
          if (["Enter", " "].includes(event.key)) {
            openFilePicker();
          }
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="visually-hidden"
          accept=".pdf,.png,.jpg,.jpeg,.webp"
          onChange={handleFileChange}
          disabled={loading}
        />
        <div className="drop-zone-content">
          <div className="upload-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" focusable="false">
              <path d="M12 16a1 1 0 0 1-1-1v-6.58l-2.3 2.3a1 1 0 1 1-1.4-1.42l4-4a1 1 0 0 1 1.4 0l4 4a1 1 0 1 1-1.4 1.42L13 8.42V15a1 1 0 0 1-1 1Z" />
              <path d="M7 19a1 1 0 1 1 0-2h10a1 1 0 1 1 0 2H7Z" />
            </svg>
          </div>
          <p>{loading ? "Envoi en cours..." : "Deposer un document"}</p>
          <small>Glisser/deposer ou cliquer pour ouvrir l'explorateur.</small>
        </div>
      </div>
      <UploadStatusBanner
        polling={polling}
        success={success}
        error={error}
        onDismiss={() => { setSuccess(""); setError(""); }}
      />
    </section>
  );
}

export default UploadPanel;
