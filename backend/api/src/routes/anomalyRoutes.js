import express from 'express';
import * as anomalyController from '../controllers/anomalyController.js';
import { protect } from '../middleware/authMiddleware.js';

const router = express.Router();

router.get('/stats', protect, anomalyController.getAnomalyStats);
router.get('/document/:documentId', protect, anomalyController.getAnomaliesByDocument);
router.get('/:id', protect, anomalyController.getAnomalyById);
router.get('/', protect, anomalyController.getAllAnomalies);
router.post('/', protect, anomalyController.createAnomaly);
router.patch('/:id/status', protect, anomalyController.updateAnomalyStatus);
router.delete('/:id', protect, anomalyController.deleteAnomaly);

export default router;
