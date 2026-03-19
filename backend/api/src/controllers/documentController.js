import {
    uploadAndTrigger,
    getDagRunStatus,
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
        res.status(200).json(status);
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
