function ConfirmModal({ open, title, message, onConfirm, onCancel }) {
  if (!open) return null;

  return (
    <div className="confirm-modal-overlay" onClick={onCancel}>
      <div className="confirm-modal" onClick={(e) => e.stopPropagation()}>
        <h3>{title}</h3>
        <p>{message}</p>
        <div className="confirm-modal-actions">
          <button type="button" className="table-action-button" onClick={onCancel}>
            Annuler
          </button>
          <button type="button" className="table-action-button danger" onClick={onConfirm}>
            Supprimer
          </button>
        </div>
      </div>
    </div>
  );
}

export default ConfirmModal;
