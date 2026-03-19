import { Router } from 'express';
import authRoutes from './authRoutes.js';
import quotationRoutes from './quotationRoutes.js';
import invoiceRoutes from './invoiceRoutes.js';
import companyRoutes from './companyRoutes.js';
import ribRoutes from './ribRoutes.js';
import kbisRoutes from './kbisRoutes.js';
import certificateEmergencyUrssafRoutes from './certificateEmergencyUrssafRoutes.js';
import documentRoutes from './documentRoutes.js';
import anomalyRoutes from './anomalyRoutes.js';
import { protect, checkRole } from '../middleware/authMiddleware.js';

const router = Router();

const comptable = [protect, checkRole('comptable')];

router.use('/auth', authRoutes);
router.use('/quotations', comptable, quotationRoutes);
router.use('/invoices', comptable, invoiceRoutes);
router.use('/companies', comptable, companyRoutes);
router.use('/ribs', comptable, ribRoutes);
router.use('/kbis', comptable, kbisRoutes);
router.use('/certificates-urssaf', comptable, certificateEmergencyUrssafRoutes);
router.use('/documents', documentRoutes);
router.use('/anomalies', comptable, anomalyRoutes);

export default router;
