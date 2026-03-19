/**
 * Bandeau de statut affiché après un upload de document.
 * Trois états : pending (analyse en cours), success, error.
 * Le bouton dismiss n'apparaît qu'une fois le traitement terminé.
 */
function UploadStatusBanner({ polling, success, error, onDismiss }) {
  if (!error && !success && !polling) return null;

  return (
    <div className={`upload-status ${error ? "error" : polling ? "pending" : "success"}`}>
      <span className="upload-status-text">
        {polling && <><strong>{polling.fileName}</strong> — Analyse en cours…</>}
        {!polling && success && <>{success}</>}
        {!polling && error && <>{error}</>}
      </span>
      {!polling && (
        <button
          className="upload-status-dismiss"
          onClick={onDismiss}
          aria-label="Fermer"
        >×</button>
      )}
    </div>
  );
}

export default UploadStatusBanner;
