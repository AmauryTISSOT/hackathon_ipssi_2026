import path from "path";
import {
    uploadAndTrigger,
    getDagRunStatus,
    getFileFromBronze,
    deleteDocument as deleteDocumentService,
} from "../services/documentService.js";
import Document from "../models/Document.js";

export const uploadDocument = async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ message: "Aucun fichier fourni" });
        }

        // req.user est ajouté
        const result = await uploadAndTrigger(req.file, req.user._id);
        res.status(201).json(result);
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
};

export const getDocumentStatus = async (req, res) => {
    try {
        const status = await getDagRunStatus(req.params.dagRunId);

        // Synchronise le statut MongoDB quand Airflow termine (succès ou échec)
        if (status.state === "failed") {
            await Document.findOneAndUpdate(
                { dag_run_id: req.params.dagRunId },
                { status: "failed" },
            );
        }

        res.status(200).json(status);
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
};

const MIME_TYPES = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".tiff": "image/tiff",
    ".tif": "image/tiff",
    ".bmp": "image/bmp",
};

export const getDocumentFile = async (req, res) => {
    try {
        const filename = req.params.filename;
        if (!filename) {
            return res.status(400).json({ message: "Nom de fichier manquant" });
        }

        const ext = path.extname(filename).toLowerCase();
        const contentType = MIME_TYPES[ext] || "application/octet-stream";

        const stream = await getFileFromBronze(filename);
        res.setHeader("Content-Type", contentType);
        res.setHeader("Content-Disposition", `inline; filename="${filename}"`);
        stream.pipe(res);
    } catch (error) {
        if (error.code === "NoSuchKey" || error.message?.includes("Not Found")) {
            return res.status(404).json({ message: "Fichier introuvable dans MinIO" });
        }
        res.status(500).json({ message: error.message });
    }
};

export const deleteDocument = async (req, res) => {
    try {
        const doc = await deleteDocumentService(req.params.id);
        if (!doc) {
            return res.status(404).json({ message: "Document introuvable" });
        }
        res.json({ message: "document deleted successfully" });
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
};

// Retourne l'historique des documents uploadés par l'utilisateur connecté
export const getHistory = async (req, res) => {
    try {
        const documents = await Document.find({ user_id: req.user._id })
            .select('filename doc_type status createdAt dag_run_id')
            .sort({ createdAt: -1 }); // du plus récent au plus ancien

        res.status(200).json({ documents });
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
};
