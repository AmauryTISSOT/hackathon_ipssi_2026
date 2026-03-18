import { Client } from "minio";

/**
 * Client MinIO singleton pour l'accès au Data Lake (buckets bronze/silver/gold).
 * Configuration via variables d'environnement, avec valeurs par défaut pour le dev local.
 */
const minioClient = new Client({
    endPoint: process.env.MINIO_ENDPOINT || "minio",
    port: parseInt(process.env.MINIO_PORT || "9000"),
    useSSL: false,
    accessKey: process.env.MINIO_ROOT_USER || "minioadmin",
    secretKey: process.env.MINIO_ROOT_PASSWORD || "minioadmin123",
});

export default minioClient;
