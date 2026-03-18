import { useEffect, useMemo, useState } from "react";
import AppLayout from "../components/AppLayout";
import { getCurrentUser } from "../services/authApi";
import { listUserDocuments } from "../services/documentApi";

const userLinks = [
  { to: "/user/recap", label: "Historique des depots" },
  { to: "/user/depot", label: "Deposer un document" }
];

function statusBadgeClass(status) {
  if (status === "Traite") return "status ok";
  if (status === "En cours") return "status pending";
  return "status error";
}

function sortByConfig(items, sortConfig) {
  return items.slice().sort((first, second) => {
    const firstValue = first[sortConfig.key];
    const secondValue = second[sortConfig.key];
    const result = String(firstValue).localeCompare(String(secondValue), "fr", {
      numeric: true
    });
    if (sortConfig.direction === "asc") return result;
    return -result;
  });
}

function normalizeDocument(document) {
  return {
    id: document.id,
    fileName: document.fileName,
    docType: document.docType,
    status: document.status,
    date: document.date
  };
}

function ClientRecapPage() {
  const currentUser = getCurrentUser();
  const [sortConfig, setSortConfig] = useState({ key: "date", direction: "desc" });
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    const loadDocuments = async () => {
      if (!currentUser) {
        setDocuments([]);
        setLoading(false);
        setError("Session invalide. Merci de vous reconnecter.");
        return;
      }

      setLoading(true);
      setError("");
      try {
        const response = await listUserDocuments();
        const items = response;
        const normalized = items.map(normalizeDocument);
        if (!cancelled) setDocuments(normalized);
      } catch {
        if (!cancelled) {
          setError("Impossible de charger les documents.");
          setDocuments([]);
        }
      }
      if (!cancelled) setLoading(false);
    };

    loadDocuments();

    return () => {
      cancelled = true;
    };
  }, [currentUser]);

  const sortedDocuments = useMemo(() => {
    return sortByConfig(documents, sortConfig);
  }, [documents, sortConfig]);

  const toggleSort = (key) => {
    setSortConfig((current) => {
      if (current.key === key) {
        return { key, direction: current.direction === "asc" ? "desc" : "asc" };
      }
      return { key, direction: "asc" };
    });
  };

  const sortLabel = (key, label) => {
    if (sortConfig.key !== key) return label;
    return `${label} ${sortConfig.direction === "asc" ? "↑" : "↓"}`;
  };

  return (
    <AppLayout title="Gestion des documents" links={userLinks}>
      <h2 className="section-title">Historique des depots</h2>
      <div className="table-wrapper">
        {loading ? <p className="message">Chargement des documents...</p> : null}
        {error ? <p className="message error">{error}</p> : null}
        <table>
          <thead>
            <tr>
              <th>
                <button type="button" className="sort-button" onClick={() => toggleSort("fileName")}>
                  {sortLabel("fileName", "Nom document")}
                </button>
              </th>
              <th>
                <button type="button" className="sort-button" onClick={() => toggleSort("docType")}>
                  {sortLabel("docType", "Type")}
                </button>
              </th>
              <th>
                <button type="button" className="sort-button" onClick={() => toggleSort("status")}>
                  {sortLabel("status", "Statut")}
                </button>
              </th>
              <th>
                <button type="button" className="sort-button" onClick={() => toggleSort("date")}>
                  {sortLabel("date", "Date")}
                </button>
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedDocuments.length > 0 ? (
              sortedDocuments.map((document) => (
                <tr key={document.id}>
                  <td>{document.fileName}</td>
                  <td>{document.docType}</td>
                  <td>
                    <span className={statusBadgeClass(document.status)}>{document.status}</span>
                  </td>
                  <td>{document.date}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={4}>
                  {loading ? "Chargement..." : "Aucun document trouve pour le moment."}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </AppLayout>
  );
}

export default ClientRecapPage;
