function DataTable({ columns, rows, loading, sortConfig, onSort, onView, onDelete, emptyMessage }) {
  const colCount = columns.length + (onView || onDelete ? 1 : 0);

  const headerLabel = (col) => {
    if (!col.sortable) return col.label;
    const arrow = sortConfig.key === col.key
      ? (sortConfig.direction === "asc" ? " ↑" : " ↓")
      : "";
    return (
      <button type="button" className="sort-button" onClick={() => onSort(col.key)}>
        {col.label}{arrow}
      </button>
    );
  };

  return (
    <div className="table-wrapper">
      <table>
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col.key}>{headerLabel(col)}</th>
            ))}
            {(onView || onDelete) && <th>Actions</th>}
          </tr>
        </thead>
        <tbody>
          {rows.length > 0 ? rows.map((row) => (
            <tr key={row.id}>
              {columns.map((col) => (
                <td key={col.key}>{row[col.key]}</td>
              ))}
              {(onView || onDelete) && (
                <td className="actions-cell">
                  {onView && (
                    <button type="button" className="table-action-button" onClick={() => onView(row)}>
                      Visualiser
                    </button>
                  )}
                  {onDelete && (
                    <button type="button" className="table-action-button danger" onClick={() => onDelete(row.id)}>
                      Supprimer
                    </button>
                  )}
                </td>
              )}
            </tr>
          )) : (
            <tr>
              <td colSpan={colCount}>{loading ? "Chargement..." : emptyMessage}</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

export default DataTable;
