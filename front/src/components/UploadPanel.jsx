import { useRef, useState, useEffect, useCallback } from "react";
import { pollDocumentStatus } from "../services/documentApi";
import UploadStatusBanner from "./UploadStatusBanner";

const MAX_FILES = 10;
const MAX_CONCURRENT = 3;
const POLL_INTERVAL = 3000;
const POLL_TIMEOUT = 5 * 60 * 1000; // 5 minutes

const ACCEPTED_TYPES = [
  "application/pdf",
  "image/png",
  "image/jpeg",
  "image/webp",
];

function UploadPanel({ onSubmit }) {
  const fileInputRef = useRef(null);
  const pollingRef = useRef({}); // { [fileId]: intervalId }
  const pollStartRef = useRef({}); // { [fileId]: timestamp }
  const [files, setFiles] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [validationError, setValidationError] = useState("");

  // Cleanup all intervals on unmount
  useEffect(() => {
    return () => {
      Object.values(pollingRef.current).forEach(clearInterval);
    };
  }, []);

  // Navigation guard
  useEffect(() => {
    const hasActive = files.some(
      (f) => f.status === "uploading" || f.status === "polling"
    );
    if (!hasActive) return;

    const handler = (e) => {
      e.preventDefault();
      e.returnValue = "";
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [files]);

  const updateFile = useCallback((id, updates) => {
    setFiles((prev) =>
      prev.map((f) => (f.id === id ? { ...f, ...updates } : f))
    );
  }, []);

  const startPolling = useCallback(
    (fileId, dagRunId) => {
      if (pollingRef.current[fileId]) return;
      pollStartRef.current[fileId] = Date.now();

      const intervalId = setInterval(async () => {
        if (Date.now() - pollStartRef.current[fileId] > POLL_TIMEOUT) {
          clearInterval(pollingRef.current[fileId]);
          delete pollingRef.current[fileId];
          delete pollStartRef.current[fileId];
          updateFile(fileId, { status: "timeout" });
          return;
        }

        try {
          const result = await pollDocumentStatus(dagRunId);
          if (result.state === "success") {
            clearInterval(pollingRef.current[fileId]);
            delete pollingRef.current[fileId];
            delete pollStartRef.current[fileId];
            updateFile(fileId, { status: "success" });
          } else if (result.state === "failed") {
            clearInterval(pollingRef.current[fileId]);
            delete pollingRef.current[fileId];
            delete pollStartRef.current[fileId];
            updateFile(fileId, {
              status: "failed",
              error: "Le traitement a échoué.",
            });
          }
        } catch {
          // keep polling
        }
      }, POLL_INTERVAL);

      pollingRef.current[fileId] = intervalId;
    },
    [updateFile]
  );

  // Queue processor: watches files state and uploads pending files when slots are free
  useEffect(() => {
    const activeCount = files.filter((f) => f.status === "uploading").length;
    const pending = files.filter((f) => f.status === "pending");
    const slotsAvailable = MAX_CONCURRENT - activeCount;

    const toUpload = pending.slice(0, slotsAvailable);
    if (toUpload.length === 0) return;

    for (const entry of toUpload) {
      // Mark as uploading
      setFiles((prev) =>
        prev.map((f) =>
          f.id === entry.id ? { ...f, status: "uploading" } : f
        )
      );

      onSubmit({ file: entry.file })
        .then((result) => {
          if (result.dagRunId) {
            updateFile(entry.id, {
              status: "polling",
              dagRunId: result.dagRunId,
              fileName: result.fileName,
            });
            startPolling(entry.id, result.dagRunId);
          } else {
            // No dagRunId means demo/fallback mode
            updateFile(entry.id, { status: "success" });
          }
        })
        .catch(() => {
          updateFile(entry.id, {
            status: "failed",
            error: "Échec de l'envoi.",
          });
        });
    }
  }, [files, onSubmit, startPolling, updateFile]);

  const addFiles = useCallback(
    (newFiles) => {
      setValidationError("");
      const fileArray = Array.from(newFiles);

      setFiles((prev) => {
        if (prev.length + fileArray.length > MAX_FILES) {
          setValidationError(`Maximum ${MAX_FILES} fichiers à la fois.`);
          return prev;
        }

        const invalid = fileArray.filter(
          (f) => !ACCEPTED_TYPES.includes(f.type)
        );
        if (invalid.length > 0) {
          setValidationError(
            `Type non accepté : ${invalid.map((f) => f.name).join(", ")}`
          );
          return prev;
        }

        const entries = fileArray.map((file) => ({
          id: crypto.randomUUID(),
          file,
          fileName: file.name,
          status: "pending",
          dagRunId: null,
          error: null,
        }));

        return [...prev, ...entries];
      });
    },
    []
  );

  const handleFileChange = (event) => {
    if (event.target.files && event.target.files.length > 0) {
      addFiles(event.target.files);
    }
    event.target.value = "";
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setIsDragging(false);
    if (event.dataTransfer.files && event.dataTransfer.files.length > 0) {
      addFiles(event.dataTransfer.files);
    }
  };

  const openFilePicker = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const isUploading = files.some(
    (f) => f.status === "uploading" || f.status === "pending"
  );

  const handleDismiss = () => {
    setFiles((prev) =>
      prev.filter(
        (f) =>
          f.status === "pending" ||
          f.status === "uploading" ||
          f.status === "polling"
      )
    );
  };

  return (
    <section className="upload-panel">
      <div
        className={isDragging ? "drop-zone dragging" : "drop-zone"}
        onClick={() => {
          if (!isUploading) openFilePicker();
        }}
        onDragOver={(event) => {
          if (isUploading) return;
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        role="button"
        tabIndex={0}
        onKeyDown={(event) => {
          if (isUploading) return;
          if (["Enter", " "].includes(event.key)) openFilePicker();
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="visually-hidden"
          accept=".pdf,.png,.jpg,.jpeg,.webp"
          multiple
          onChange={handleFileChange}
          disabled={isUploading}
        />
        <div className="drop-zone-content">
          <div className="upload-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" focusable="false">
              <path d="M12 16a1 1 0 0 1-1-1v-6.58l-2.3 2.3a1 1 0 1 1-1.4-1.42l4-4a1 1 0 0 1 1.4 0l4 4a1 1 0 1 1-1.4 1.42L13 8.42V15a1 1 0 0 1-1 1Z" />
              <path d="M7 19a1 1 0 1 1 0-2h10a1 1 0 1 1 0 2H7Z" />
            </svg>
          </div>
          <p>{isUploading ? "Envoi en cours..." : "Deposer des documents"}</p>
          <small>
            Glisser/deposer ou cliquer pour ouvrir l'explorateur (max{" "}
            {MAX_FILES} fichiers).
          </small>
        </div>
      </div>
      {validationError && (
        <div className="upload-status error">
          <span className="upload-status-text">{validationError}</span>
          <button
            className="upload-status-dismiss"
            onClick={() => setValidationError("")}
            aria-label="Fermer"
          >
            ×
          </button>
        </div>
      )}
      <UploadStatusBanner files={files} onDismiss={handleDismiss} />
    </section>
  );
}

export default UploadPanel;
