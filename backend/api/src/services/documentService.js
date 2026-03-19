import axios from "axios";
import minioClient from "../config/minio.js";
import Document from "../models/Document.js";

/** URL de l'API Airflow (hostname Docker en prod, localhost en dev) */
const AIRFLOW_API_URL =
    process.env.AIRFLOW_API_URL || "http://airflow-api-server:8080";
const AIRFLOW_USER = process.env.AIRFLOW_USER || "admin";
const AIRFLOW_PASSWORD = process.env.AIRFLOW_PASSWORD || "admin";

/** Token JWT Airflow mis en cache pour éviter un appel auth à chaque requête */
let cachedToken = null;
let tokenExpiry = 0;

/**
 * Obtient un token JWT depuis l'API Airflow 3 (POST /auth/token).
 * Le token est mis en cache et renouvelé automatiquement après 23h.
 * @returns {Promise<string>} Token JWT valide
 */
const getAirflowToken = async () => {
    if (cachedToken && Date.now() < tokenExpiry) {
        return cachedToken;
    }

    const response = await axios.post(`${AIRFLOW_API_URL}/auth/token`, {
        username: AIRFLOW_USER,
        password: AIRFLOW_PASSWORD,
    });

    cachedToken = response.data.access_token;
    tokenExpiry = Date.now() + 23 * 60 * 60 * 1000;
    return cachedToken;
};

/**
 * Exécute une requête authentifiée vers l'API Airflow.
 * @param {string} method - Méthode HTTP (get, post, etc.)
 * @param {string} url - URL complète de l'endpoint Airflow
 * @param {object} [data] - Corps de la requête (optionnel)
 * @returns {Promise<import('axios').AxiosResponse>}
 */
const airflowRequest = async (method, url, data) => {
    const token = await getAirflowToken();
    return axios({
        method,
        url,
        data,
        headers: { Authorization: `Bearer ${token}` },
    });
};

/**
 * Upload un fichier dans MinIO (bucket bronze) puis déclenche le DAG Airflow document_pipeline.
 * Crée également une entrée dans MongoDB pour suivre l'historique de l'utilisateur.
 * @param {object} file - Objet fichier multer (req.file) avec buffer et originalname
 * @param {string} userId - ID de l'utilisateur connecté (req.user._id)
 * @returns {Promise<{dag_run_id: string, doc_name: string}>} Identifiants du DAG run créé
 */
export const uploadAndTrigger = async (file, userId) => {
    // Upload du document brut dans le bucket bronze (première couche du Data Lake)
    await minioClient.putObject("bronze", file.originalname, file.buffer);

    const response = await airflowRequest(
        "post",
        `${AIRFLOW_API_URL}/api/v2/dags/document_pipeline/dagRuns`,
        {
            conf: { doc_name: file.originalname },
            logical_date: new Date().toISOString(),
        },
    );

    const dagRunId = response.data.dag_run_id;

    // On sauvegarde le document avec status "pending"
    // Airflow mettra à jour le status à "processed" une fois le pipeline terminé
    await Document.create({
        filename: file.originalname,
        status: 'pending',
        user_id: userId,
        dag_run_id: dagRunId,
    });

    return {
        dag_run_id: dagRunId,
        doc_name: file.originalname,
    };
};

/**
 * Récupère le statut d'un DAG run Airflow (proxy vers l'API REST Airflow).
 * @param {string} dagRunId - Identifiant du DAG run
 * @returns {Promise<object>} Statut complet du DAG run (state, start_date, end_date, etc.)
 */

/**
 * Récupère un fichier depuis le bucket bronze de MinIO sous forme de stream.
 * @param {string} filename - Nom du fichier dans le bucket bronze
 * @returns {Promise<import('stream').Readable>} Stream du fichier
 */
export const getFileFromBronze = async (filename) => {
    return minioClient.getObject("bronze", filename);
};

export const getDagRunStatus = async (dagRunId) => {
    const response = await airflowRequest(
        "get",
        `${AIRFLOW_API_URL}/api/v2/dags/document_pipeline/dagRuns/${dagRunId}`,
    );

    return response.data;
};
