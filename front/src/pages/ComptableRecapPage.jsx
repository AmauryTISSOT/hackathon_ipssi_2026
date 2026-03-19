import { useEffect, useMemo, useState } from "react";
import AppLayout from "../components/AppLayout";
import DataTable from "../components/DataTable";
import {
  listInvoices,
  listQuotations,
  listKbis,
  listCertificates,
  listRibs,
  listFailedDocuments,
  listAllDocuments,
  listFolders,
  deleteInvoice,
  deleteQuotation,
  deleteKbis,
  deleteCertificate,
  deleteRib,
  getDocumentFileUrl,
} from "../services/documentApi";

const comptableLinks = [
  { to: "/comptable/gestion", label: "Gestion des documents" },
  { to: "/comptable/depot", label: "Deposer un document" }
];

const tableTabs = [
  "Facture fournisseur",
  "Devis",
  "KBIS",
  "Attestation URSSAF",
  "Document non conforme",
  "RIB",
  "Dossiers"
];

function normalizeInvoice(doc) {
  const company = doc.company_id;
  return {
    id: doc._id,
    fileName: company?.denomination_unite_legale ?? "-",
    siret: company?.siret ?? "-",
    tva: doc.total_tax != null ? `${doc.total_tax}€` : "-",
    amount: doc.total_before_tax != null ? `${doc.total_before_tax}€ / ${doc.total}€` : "-",
    date: doc.issue_date ? doc.issue_date.slice(0, 10) : "-",
    ownerName: company?.denomination_unite_legale ?? "-",
    sourceFilename: doc.source_filename,
  };
}

function normalizeQuotation(doc) {
  const company = doc.company_id;
  return {
    id: doc._id,
    fileName: doc.label ?? "-",
    siret: company?.siret ?? "-",
    tva: doc.total_tva != null ? `${doc.total_tva}€` : "-",
    amount: doc.total_before_tax != null ? `${doc.total_before_tax}€ / ${doc.total}€` : "-",
    date: doc.issue_date ? doc.issue_date.slice(0, 10) : "-",
    ownerName: doc.issuer?.name ?? "-",
    sourceFilename: doc.source_filename,
  };
}

function normalizeKbis(doc) {
  const legal = doc.legal_entity ?? {};
  const activity = doc.information_relating_activity_main_establishment ?? {};
  return {
    id: doc._id,
    trading_name: activity.trading_name ?? "-",
    establishment_address: activity.establishment_address ?? "-",
    legal_form: legal.legal_form ?? "-",
    sourceFilename: doc.source_filename,
  };
}

function normalizeCertificate(doc) {
  return {
    id: doc._id,
    siret: doc.siret ?? "-",
    security_code: doc.security_code ?? "-",
    international_identifier: doc.international_identifier ?? "-",
    place_at: doc.place_at ? String(doc.place_at).slice(0, 10) : "-",
    siren: doc.siren ?? "-",
    social_security: doc.social_security ?? "-",
    sourceFilename: doc.source_filename,
  };
}

function normalizeRib(doc) {
  const company = doc.company_id;
  return {
    id: doc._id,
    iban: doc.iban ?? "-",
    bic: doc.bic ?? "-",
    bank_code: doc.bank_code ?? "-",
    agency_code: doc.agency_code ?? "-",
    account_number: doc.account_number ?? "-",
    key: doc.key ?? "-",
    registered_address: doc.registered_address ?? "-",
    siret: company?.siret ?? "-",
    date: doc.createdAt ? doc.createdAt.slice(0, 10) : "-",
    sourceFilename: doc.source_filename,
  };
}

function normalizeFailedDoc(doc) {
  return {
    id: doc._id,
    fileName: doc.filename ?? "-",
    date: doc.createdAt ? doc.createdAt.slice(0, 10) : "-",
  };
}

function normalizeDossierDoc(doc) {
  return {
    id: doc.id,
    fileName: doc.fileName,
    docType: doc.docType,
    date: doc.date,
    folder: doc.folder,
  };
}

const TAB_CONFIG = {
  "Facture fournisseur": {
    fetch: listInvoices,
    delete: deleteInvoice,
    normalize: normalizeInvoice,
    columns: [
      { key: "fileName", label: "Nom document", sortable: true },
      { key: "siret", label: "SIRET" },
      { key: "tva", label: "TVA" },
      { key: "amount", label: "Montant HT/TTC" },
      { key: "date", label: "Date", sortable: true },
      { key: "ownerName", label: "Proprietaire", sortable: true },
    ],
    showView: true,
    emptyMessage: "Aucune facture trouvee.",
  },
  "Devis": {
    fetch: listQuotations,
    delete: deleteQuotation,
    normalize: normalizeQuotation,
    columns: [
      { key: "fileName", label: "Libelle", sortable: true },
      { key: "siret", label: "SIRET" },
      { key: "tva", label: "TVA" },
      { key: "amount", label: "Montant HT/TTC" },
      { key: "date", label: "Date", sortable: true },
      { key: "ownerName", label: "Emetteur", sortable: true },
    ],
    showView: true,
    emptyMessage: "Aucun devis trouve.",
  },
  "KBIS": {
    fetch: listKbis,
    delete: deleteKbis,
    normalize: normalizeKbis,
    columns: [
      { key: "trading_name", label: "Nom d'entite", sortable: true },
      { key: "establishment_address", label: "Adresse" },
      { key: "legal_form", label: "Entite legale", sortable: true },
    ],
    showView: true,
    emptyMessage: "Aucun KBIS trouve.",
  },
  "Attestation URSSAF": {
    fetch: listCertificates,
    delete: deleteCertificate,
    normalize: normalizeCertificate,
    columns: [
      { key: "siret", label: "SIRET", sortable: true },
      { key: "siren", label: "SIREN" },
      { key: "security_code", label: "Code securite" },
      { key: "international_identifier", label: "Identifiant international" },
      { key: "social_security", label: "Securite sociale" },
      { key: "place_at", label: "Adresse", sortable: true },
    ],
    showView: true,
    emptyMessage: "Aucune attestation URSSAF trouvee.",
  },
  "Document non conforme": {
    fetch: listFailedDocuments,
    normalize: normalizeFailedDoc,
    columns: [
      { key: "fileName", label: "Nom document", sortable: true },
      { key: "date", label: "Date", sortable: true },
    ],
    showView: false,
    emptyMessage: "Aucun document non conforme.",
  },
  "RIB": {
    fetch: listRibs,
    delete: deleteRib,
    normalize: normalizeRib,
    columns: [
      { key: "iban", label: "IBAN", sortable: true },
      { key: "bic", label: "BIC" },
      { key: "bank_code", label: "Code banque" },
      { key: "agency_code", label: "Code guichet" },
      { key: "account_number", label: "N° compte" },
      { key: "key", label: "Cle RIB" },
      { key: "registered_address", label: "Adresse" },
    ],
    showView: true,
    emptyMessage: "Aucun RIB trouve.",
  },
};

const DOSSIERS_COLUMNS = [
  { key: "fileName", label: "Nom document", sortable: true },
  { key: "docType", label: "Type", sortable: true },
  { key: "date", label: "Date", sortable: true },
  { key: "folder", label: "Dossier", sortable: true },
];

function sortByConfig(items, sortConfig) {
  return items.slice().sort((first, second) => {
    const firstValue = first[sortConfig.key];
    const secondValue = second[sortConfig.key];
    const result = String(firstValue).localeCompare(String(secondValue), "fr", { numeric: true });
    return sortConfig.direction === "asc" ? result : -result;
  });
}

function buildFoldersFromDocuments(documents) {
  const byFolder = documents.reduce((acc, doc) => {
    if (!acc[doc.folder]) acc[doc.folder] = 0;
    acc[doc.folder] += 1;
    return acc;
  }, {});
  return Object.entries(byFolder).map(([name, count]) => ({ name, count }));
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
    setLoading(true);
    setError("");
    setDocuments([]);

    const loadData = async () => {
      try {
        if (activeTab === "Dossiers") {
          const [docsResponse, foldersResponse] = await Promise.all([
            listAllDocuments(),
            listFolders(),
          ]);
          if (!cancelled) {
            setDocuments(docsResponse.map(normalizeDossierDoc));
            setFolders(foldersResponse);
          }
        } else {
          const config = TAB_CONFIG[activeTab];
          const items = await config.fetch();
          if (!cancelled) {
            setDocuments((items ?? []).map(config.normalize));
          }
        }
      } catch {
        if (!cancelled) {
          setError("Impossible de charger les documents.");
        }
      }
      if (!cancelled) setLoading(false);
    };

    loadData();
    return () => { cancelled = true; };
  }, [activeTab]);

  const filteredDocuments = useMemo(() => {
    let scoped = documents;
    if (activeTab === "Dossiers" && selectedFolder !== "Tous") {
      scoped = scoped.filter((doc) => doc.folder === selectedFolder);
    }
    return sortByConfig(scoped, sortConfig);
  }, [activeTab, documents, selectedFolder, sortConfig]);

  const toggleSort = (key) => {
    setSortConfig((current) => ({
      key,
      direction: current.key === key && current.direction === "asc" ? "desc" : "asc",
    }));
  };

  const handleViewDocument = (document) => {
    if (document.sourceFilename) {
      const url = getDocumentFileUrl(document.sourceFilename);
      window.open(url, "_blank", "noopener,noreferrer");
      return;
    }
    window.alert(`Apercu indisponible pour "${document.fileName || document.id}".`);
  };

  const handleDeleteDocument = async (documentId) => {
    const config = TAB_CONFIG[activeTab];
    if (config?.delete) {
      try {
        await config.delete(documentId);
      } catch {
        setError("Impossible de supprimer le document.");
        return;
      }
    }
    setDocuments((current) => {
      const updated = current.filter((doc) => doc.id !== documentId);
      setFolders(buildFoldersFromDocuments(updated));
      if (selectedFolder !== "Tous" && !updated.some((doc) => doc.folder === selectedFolder)) {
        setSelectedFolder("Tous");
      }
      return updated;
    });
  };

  return (
    <AppLayout title="Gestion des documents" links={comptableLinks}>
      {error ? <p className="message error">{error}</p> : null}

      <div className="tabs">
        {tableTabs.map((tab) => (
          <button
            key={tab}
            type="button"
            className={tab === activeTab ? "tab-button active" : "tab-button"}
            onClick={() => { setActiveTab(tab); setSelectedFolder("Tous"); }}
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
          <DataTable
            columns={DOSSIERS_COLUMNS}
            rows={filteredDocuments}
            loading={loading}
            sortConfig={sortConfig}
            onSort={toggleSort}
            onView={handleViewDocument}
            onDelete={handleDeleteDocument}
            emptyMessage="Aucun document pour ce filtre."
          />
        </>
      ) : (
        <DataTable
          columns={TAB_CONFIG[activeTab].columns}
          rows={filteredDocuments}
          loading={loading}
          sortConfig={sortConfig}
          onSort={toggleSort}
          onView={TAB_CONFIG[activeTab].showView ? handleViewDocument : undefined}
          onDelete={handleDeleteDocument}
          emptyMessage={TAB_CONFIG[activeTab].emptyMessage}
        />
      )}
    </AppLayout>
  );
}

export default ComptableRecapPage;
