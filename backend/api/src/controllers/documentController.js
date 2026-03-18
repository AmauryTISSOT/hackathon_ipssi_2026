import {
    uploadAndTrigger,
    getDagRunStatus,
} from "../services/documentService.js";

/**
 * Upload un document dans MinIO (bronze) et déclenche le DAG Airflow.
 * @param {import('express').Request} req - Requête Express avec fichier multer (req.file)
 * @param {import('express').Response} res - Réponse Express
 * @returns {Promise<void>} 201 avec { dag_run_id, doc_name } ou 400/500 en cas d'erreur
 */
export const uploadDocument = async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ message: "Aucun fichier fourni" });
        }

        const result = await uploadAndTrigger(req.file);
        res.status(201).json(result);
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
};

/**
 * Récupère le statut d'un DAG run Airflow.
 * @param {import('express').Request} req - Requête Express avec req.params.dagRunId
 * @param {import('express').Response} res - Réponse Express
 * @returns {Promise<void>} 200 avec le statut du DAG run ou 500 en cas d'erreur
 */
export const getDocumentStatus = async (req, res) => {
    try {
        const status = await getDagRunStatus(req.params.dagRunId);
        res.status(200).json(status);
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
};
