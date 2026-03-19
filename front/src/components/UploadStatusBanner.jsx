const STATUS_LABELS = {
  pending: "En attente",
  uploading: "Envoi…",
  polling: "Analyse en cours…",
  success: "Traité",
  failed: "Échoué",
  timeout: "Délai dépassé",
};


function UploadStatusBanner({ files, onDismiss }) {
  if (!files || files.length === 0) return null;

  const completed = files.filter(
    (f) => f.status === "success" || f.status === "failed" || f.status === "timeout"
  );
  const allDone = completed.length === files.length;

  return (
    <div className="upload-status-multi">
      <div className="upload-status-header">
        <span>
          {completed.length}/{files.length} terminé{completed.length > 1 ? "s" : ""}
        </span>
        {allDone && (
          <button
            className="upload-status-dismiss"
            onClick={onDismiss}
            aria-label="Fermer"
          >
            ×
          </button>
        )}
      </div>
      <ul className="upload-status-list">
        {files.map((f) => (
          <li key={f.id} className={`upload-status-item ${f.status}`}>
            <span className="upload-status-name">{f.fileName}</span>
            <span className="upload-status-label">
              {f.error || STATUS_LABELS[f.status]}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default UploadStatusBanner;
