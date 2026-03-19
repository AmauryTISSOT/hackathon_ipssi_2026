import { getAuthToken, getCurrentUser } from "./authApi";

const API_URL = import.meta.env.VITE_API_URL;
const DOCUMENTS_KEY = "demo_documents";

const seedDocuments = [
  {
    id: "doc-1",
    ownerEmail: "user@demo.fr",
    ownerName: "User Demo",
    fileName: "Facture_16_03.pdf",
    docType: "Facture fournisseur",
    status: "Traite",
    siret: "12452154",
    tva: "20%",
    amount: "8330EUR - 8500EUR",
    date: "2026-03-16",
    folder: "Dossier mars"
  },
  {
    id: "doc-2",
    ownerEmail: "user@demo.fr",
    ownerName: "User Demo",
    fileName: "Attestation_urssaf.png",
    docType: "Attestation SIRET",
    status: "En cours",
    siret: "12452154",
    tva: "-",
    amount: "-",
    date: "2026-03-16",
    folder: "Dossier mars"
  },
  {
    id: "doc-3",
    ownerEmail: "user@demo.fr",
    ownerName: "User Demo",
    fileName: "RIB_fournisseur.pdf",
    docType: "RIB",
    status: "Non conforme",
    siret: "12452154",
    tva: "-",
    amount: "-",
    date: "2026-03-16",
    folder: "A verifier"
  },
  {
    id: "doc-4",
    ownerEmail: "comptable@demo.fr",
    ownerName: "Comptable Demo",
    fileName: "Devis_2026_03.pdf",
    docType: "Devis",
    status: "Traite",
    siret: "77889966",
    tva: "20%",
    amount: "1200EUR - 1440EUR",
    date: "2026-03-15",
    folder: "Classement Q1"
  }
];

function readDemoDocuments() {
  try {
    const raw = JSON.parse(localStorage.getItem(DOCUMENTS_KEY));
    if (Array.isArray(raw) && raw.length > 0) {
      return raw;
    }
    localStorage.setItem(DOCUMENTS_KEY, JSON.stringify(seedDocuments));
    return seedDocuments;
  } catch {
    localStorage.setItem(DOCUMENTS_KEY, JSON.stringify(seedDocuments));
    return seedDocuments;
  }
}

function writeDemoDocuments(documents) {
  localStorage.setItem(DOCUMENTS_KEY, JSON.stringify(documents));
}

function inferDocType(fileName) {
  const lowered = fileName.toLowerCase();
  if (lowered.includes("devis")) return "Devis";
  if (lowered.includes("attestation")) return "Attestation SIRET";
  if (lowered.includes("siret")) return "Attestation SIRET";
  if (lowered.includes("rib")) return "RIB";
  if (lowered.includes("nonconforme")) return "Document non conforme";
  if (lowered.includes("non_conforme")) return "Document non conforme";
  return "Facture fournisseur";
}

function inferStatus(fileName) {
  const lowered = fileName.toLowerCase();
  if (lowered.includes("nonconforme")) return "Non conforme";
  if (lowered.includes("erreur")) return "Non conforme";
  if (lowered.includes("scan")) return "En cours";
  if (lowered.includes("processing")) return "En cours";
  return "Traite";
}

function inferFolder(docType) {
  if (docType === "Facture fournisseur") return "Factures";
  if (docType === "Devis") return "Devis";
  if (docType === "Attestation SIRET") return "Conformite";
  if (docType === "RIB") return "Banque";
  return "A verifier";
}

async function request(path, { method = "GET", body, token, isFormData = false } = {}) {
  const headers = {};
  if (!isFormData) {
    headers["Content-Type"] = "application/json";
  }
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const options = {
    method,
    headers
  };
  if (body !== undefined) {
    options.body = isFormData ? body : JSON.stringify(body);
  }

  const response = await fetch(`${API_URL}${path}`, options);

  let data = {};
  try {
    data = await response.json();
  } catch {
    data = {};
  }

  if (!response.ok) {
    throw new Error(data.message);
  }
  return data;
}

export function getDocumentFileUrl(filename) {
  const token = getAuthToken();
  return `${API_URL}/api/documents/file/${encodeURIComponent(filename)}?token=${token}`;
}

export async function pollDocumentStatus(dagRunId) {
  const token = getAuthToken();
  return request(`/api/documents/status/${dagRunId}`, { token });
}

export async function createDocument({ file }) {
  const token = getAuthToken();
  const formData = new FormData();
  formData.append("file", file);
  try {
    const response = await request("/api/documents/upload", {
      method: "POST",
      body: formData,
      token,
      isFormData: true
    });

    // L'API renvoie { dag_run_id, doc_name } — on normalise pour le composant
    return {
      fileName: response.doc_name,
      dagRunId: response.dag_run_id,
      status: "pending"
    };
  } catch {
    const currentUser = getCurrentUser();
    if (!currentUser) {
      throw new Error("Session invalide. Merci de vous reconnecter.");
    }

    const fileName = file.name.trim();
    const docType = inferDocType(fileName);
    let tva = "-";
    let amount = "-";
    if (docType === "Facture fournisseur") {
      tva = "20%";
      amount = "1500EUR - 1800EUR";
    }
    if (docType === "Devis") {
      tva = "20%";
      amount = "1500EUR - 1800EUR";
    }
    const created = {
      id: crypto.randomUUID(),
      ownerEmail: currentUser.email,
      ownerName: currentUser.fullName,
      fileName,
      docType,
      status: inferStatus(fileName),
      siret: "12452154",
      tva,
      amount,
      date: new Date().toISOString().slice(0, 10),
      folder: inferFolder(docType)
    };

    const documents = readDemoDocuments();
    documents.unshift(created);
    writeDemoDocuments(documents);
    return created;
  }
}

export async function listUserDocuments() {
  const token = getAuthToken();
  try {
    const response = await request("/api/documents/history", { token });
    return response.documents;
  } catch {
    const currentUser = getCurrentUser();
    const ownerEmail = currentUser ? currentUser.email : "";
    if (!ownerEmail) return [];
    return readDemoDocuments().filter((document) => document.ownerEmail === ownerEmail);
  }
}

export async function listAllDocuments() {
  const token = getAuthToken();
  try {
    const response = await request("/api/documents", { token });
    return response.documents;
  } catch {
    return readDemoDocuments();
  }
}

export async function listFolders() {
  const token = getAuthToken();
  try {
    const response = await request("/api/documents/folders", { token });
    return response.folders;
  } catch {
    const byFolder = readDemoDocuments().reduce((accumulator, document) => {
      if (!accumulator[document.folder]) {
        accumulator[document.folder] = 0;
      }
      accumulator[document.folder] += 1;
      return accumulator;
    }, {});
    return Object.entries(byFolder).map(([name, count]) => ({ name, count }));
  }
}

export async function listInvoices() {
  const token = getAuthToken();
  const response = await request("/api/invoices", { token });
  return response.invoices;
}

export async function listQuotations() {
  const token = getAuthToken();
  const response = await request("/api/quotations", { token });
  return response.quotations;
}

export async function listKbis() {
  const token = getAuthToken();
  const response = await request("/api/kbis", { token });
  return response.kbis;
}

export async function listCertificates() {
  const token = getAuthToken();
  const response = await request("/api/certificates-urssaf", { token });
  return response.certificates;
}

export async function listRibs() {
  const token = getAuthToken();
  const response = await request("/api/ribs", { token });
  return response.ribs;
}

export async function listFailedDocuments() {
  const token = getAuthToken();
  const response = await request("/api/documents/history", { token });
  return (response.documents || []).filter((d) => d.status === "failed");
}

export async function deleteInvoice(id) {
  const token = getAuthToken();
  return request(`/api/invoices/${id}`, { method: "DELETE", token });
}

export async function deleteQuotation(id) {
  const token = getAuthToken();
  return request(`/api/quotations/${id}`, { method: "DELETE", token });
}

export async function deleteKbis(id) {
  const token = getAuthToken();
  return request(`/api/kbis/${id}`, { method: "DELETE", token });
}

export async function deleteCertificate(id) {
  const token = getAuthToken();
  return request(`/api/certificates-urssaf/${id}`, { method: "DELETE", token });
}

export async function deleteRib(id) {
  const token = getAuthToken();
  return request(`/api/ribs/${id}`, { method: "DELETE", token });
}
