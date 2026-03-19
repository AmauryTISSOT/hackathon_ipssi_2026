import { Router } from "express";
import multer, { memoryStorage } from "multer";
import { protect } from "../middleware/authMiddleware.js";
import {
    uploadDocument,
    getDocumentStatus,
    getDocumentFile,
    getHistory,
} from "../controllers/documentController.js";

const router = Router();

/** Stockage en mémoire : le fichier reste en buffer (req.file.buffer) sans écriture disque */
const upload = multer({ storage: memoryStorage() });

/**
 * POST /api/documents/upload
 * Upload un document (multipart/form-data, champ "file") → MinIO bronze + trigger DAG Airflow.
 * Authentification requise (JWT Bearer token).
 */
router.post("/upload", protect, upload.single("file"), uploadDocument);

/**
 * GET /api/documents/status/:dagRunId
 * Récupère le statut d'exécution du pipeline Airflow pour un DAG run donné.
 * Authentification requise (JWT Bearer token).
 */
router.get("/status/:dagRunId", protect, getDocumentStatus);

/**
 * GET /api/documents/history
 * Retourne la liste des documents uploadés par l'utilisateur connecté.
 * Authentification requise (JWT Bearer token).
 */
router.get("/history", protect, getHistory);

/**
 * GET /api/documents/file/:filename
 * Streame un fichier depuis le bucket bronze de MinIO.
 * Supporte le token JWT via query param (?token=xxx) pour window.open().
 */
router.get("/file/:filename", protect, getDocumentFile);

export default router;
