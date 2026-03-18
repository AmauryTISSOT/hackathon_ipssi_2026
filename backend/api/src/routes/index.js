import { Router } from 'express';
import authRoutes from './authRoutes.js';
import quotationRoutes from './quotationRoutes.js';
import invoiceRoutes from './invoiceRoutes.js';
import companyRoutes from './companyRoutes.js';
import ribRoutes from './ribRoutes.js';
import kbisRoutes from './kbisRoutes.js';
import certificateEmergencyUrssafRoutes from './certificateEmergencyUrssafRoutes.js';
import documentRoutes from './documentRoutes.js';

const router = Router();

router.use('/auth', authRoutes);
router.use('/quotations', quotationRoutes);
router.use('/invoices', invoiceRoutes);
router.use('/companies', companyRoutes);
router.use('/ribs', ribRoutes);
router.use('/kbis', kbisRoutes);
router.use('/certificates-urssaf', certificateEmergencyUrssafRoutes);
router.use('/documents', documentRoutes);

export default router;
