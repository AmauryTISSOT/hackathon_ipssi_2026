import { useEffect, useMemo, useState } from "react";
import AppLayout from "../components/AppLayout";
import { listAllDocuments, listFolders } from "../services/documentApi";

const comptableLinks = [
  { to: "/comptable/gestion", label: "Gestion des documents" },
  { to: "/comptable/depot", label: "Deposer un document" }
];

const tableTabs = [
  "Facture fournisseur",
  "Devis",
  "Attestation SIRET",
  "Document non conforme",
  "RIB",
  "Dossiers"
];

function normalizeDocument(document) {
  return {
    id: document.id,
    fileName: document.fileName,
    docType: document.docType,
    date: document.date,
    folder: document.folder,
    siret: document.siret,
    tva: document.tva,
    amount: document.amount,
    ownerName: document.ownerName
  };
}

function buildFoldersFromDocuments(documents) {
  const byFolder = documents.reduce((accumulator, document) => {
    const folderName = document.folder;
    if (!accumulator[folderName]) {
      accumulator[folderName] = 0;
    }
    accumulator[folderName] += 1;
    return accumulator;
  }, {});

  return Object.entries(byFolder).map(([name, count]) => ({ name, count }));
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

function ComptableRecapPage() {
  const [activeTab, setActiveTab] = useState("Facture fournisseur");
  const [selectedFolder, setSelectedFolder] = useState("Tous");
  const [sortConfig, setSortConfig] = useState({ key: "date", direction: "desc" });
  const [documents, setDocuments] = useState([]);
  const [folders, setFolders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    const loadData = async () => {
      setLoading(true);
      setError("");
      try {
        const docsResponse = await listAllDocuments();
        const foldersResponse = await listFolders();
        if (!cancelled) {
          setDocuments(docsResponse.map(normalizeDocument));
          setFolders(foldersResponse);
        }
      } catch {
        if (!cancelled) {
          setError("Impossible de charger les documents.");
          setDocuments([]);
          setFolders([]);
        }
      }
      if (!cancelled) setLoading(false);
    };

    loadData();
    return () => {
      cancelled = true;
    };
  }, []);

  const filteredDocuments = useMemo(() => {
    let scopedDocuments =
      activeTab === "Dossiers"
        ? documents
        : documents.filter((document) => document.docType === activeTab);

    if (activeTab === "Dossiers" && selectedFolder !== "Tous") {
      scopedDocuments = scopedDocuments.filter((document) => document.folder === selectedFolder);
    }

    return sortByConfig(scopedDocuments, sortConfig);
  }, [activeTab, documents, selectedFolder, sortConfig]);

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

  const handleViewDocument = (document) => {
    const fileUrl = document.fileUrl;
    if (fileUrl) {
      window.open(fileUrl, "_blank", "noopener,noreferrer");
      return;
    }

    window.alert(`Apercu indisponible pour "${document.fileName}".`);
  };

  const handleDeleteDocument = (documentId) => {
    setDocuments((currentDocuments) => {
      const updatedDocuments = currentDocuments.filter((document) => document.id !== documentId);
      setFolders(buildFoldersFromDocuments(updatedDocuments));
      if (selectedFolder !== "Tous" && !updatedDocuments.some((doc) => doc.folder === selectedFolder)) {
        setSelectedFolder("Tous");
      }
      return updatedDocuments;
    });
  };

  return (
    <AppLayout title="Gestion des documents" links={comptableLinks}>
      {loading ? <p className="message">Chargement des documents...</p> : null}
      {error ? <p className="message error">{error}</p> : null}
      <div className="tabs">
        {tableTabs.map((tab) => (
          <button
            key={tab}
            type="button"
            className={tab === activeTab ? "tab-button active" : "tab-button"}
            onClick={() => {
              setActiveTab(tab);
              setSelectedFolder("Tous");
            }}
          >
            {tab}
          </button>
        ))}
      </div>

      {activeTab === "Dossiers" ? (
        <>
          <div className="folder-grid">
            <button
              type="button"
              className={selectedFolder === "Tous" ? "folder-card active" : "folder-card"}
              onClick={() => setSelectedFolder("Tous")}
            >
              <p className="folder-icon">📁</p>
              <p>Tous</p>
              <small>{documents.length} document(s)</small>
            </button>
            {folders.map((folder) => (
              <button
                key={folder.name}
                type="button"
                className={selectedFolder === folder.name ? "folder-card active" : "folder-card"}
                onClick={() => setSelectedFolder(folder.name)}
              >
                <p className="folder-icon">📁</p>
                <p>{folder.name}</p>
                <small>{folder.count} document(s)</small>
              </button>
            ))}
          </div>

          <div className="table-wrapper">
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
                    <button type="button" className="sort-button" onClick={() => toggleSort("date")}>
                      {sortLabel("date", "Date")}
                    </button>
                  </th>
                  <th>
                    <button type="button" className="sort-button" onClick={() => toggleSort("folder")}>
                      {sortLabel("folder", "Dossier")}
                    </button>
                  </th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredDocuments.length > 0 ? (
                  filteredDocuments.map((document) => (
                    <tr key={document.id}>
                      <td>{document.fileName}</td>
                      <td>{document.docType}</td>
                      <td>{document.date}</td>
                      <td>{document.folder}</td>
                      <td className="actions-cell">
                        <button
                          type="button"
                          className="table-action-button"
                          onClick={() => handleViewDocument(document)}
                        >
                          Visualiser
                        </button>
                        <button
                          type="button"
                          className="table-action-button danger"
                          onClick={() => handleDeleteDocument(document.id)}
                        >
                          Supprimer
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5}>
                      {loading ? "Chargement..." : "Aucun document trouve pour ce filtre."}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>
                  <button type="button" className="sort-button" onClick={() => toggleSort("fileName")}>
                    {sortLabel("fileName", "Nom document")}
                  </button>
                </th>
                <th>SIRET</th>
                <th>TVA</th>
                <th>Montant HT/TTC</th>
                <th>
                  <button type="button" className="sort-button" onClick={() => toggleSort("date")}>
                    {sortLabel("date", "Date")}
                  </button>
                </th>
                <th>
                  <button type="button" className="sort-button" onClick={() => toggleSort("ownerName")}>
                    {sortLabel("ownerName", "Proprietaire")}
                  </button>
                </th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredDocuments.length > 0 ? (
                filteredDocuments.map((document) => (
                  <tr key={document.id}>
                    <td>{document.fileName}</td>
                    <td>{document.siret}</td>
                    <td>{document.tva}</td>
                    <td>{document.amount}</td>
                    <td>{document.date}</td>
                    <td>{document.ownerName}</td>
                    <td className="actions-cell">
                      <button
                        type="button"
                        className="table-action-button"
                        onClick={() => handleViewDocument(document)}
                      >
                        Visualiser
                      </button>
                      <button
                        type="button"
                        className="table-action-button danger"
                        onClick={() => handleDeleteDocument(document.id)}
                      >
                        Supprimer
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7}>Aucune donnee pour ce type de document.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </AppLayout>
  );
}

export default ComptableRecapPage;
