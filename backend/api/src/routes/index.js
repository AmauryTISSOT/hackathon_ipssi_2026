import { Router } from 'express';
import quotationRoutes from './quotationRoutes.js';
import invoiceRoutes from './invoiceRoutes.js';
import companyRoutes from './companyRoutes.js';
import ribRoutes from './ribRoutes.js';
import kbisRoutes from './kbisRoutes.js';
import certificateEmergencyUrssafRoutes from './certificateEmergencyUrssafRoutes.js';

const router = Router();

router.use('/quotations', quotationRoutes);
router.use('/invoices', invoiceRoutes);
router.use('/companies', companyRoutes);
router.use('/ribs', ribRoutes);
router.use('/kbis', kbisRoutes);
router.use('/certificates-urssaf', certificateEmergencyUrssafRoutes);

export default router;
