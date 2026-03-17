import { Router } from 'express';
import {
  createCertificateEmergencyUrssaf,
  getAllCertificatesEmergencyUrssaf,
  getCertificateEmergencyUrssafById,
  getCertificateEmergencyUrssafByCompany,
  getCertificateEmergencyUrssafBySIREN,
  getCertificateEmergencyUrssafBySIRET,
  updateCertificateEmergencyUrssaf,
  deleteCertificateEmergencyUrssaf
} from '../controllers/certificateEmergencyUrssafController.js';

const router = Router();

router.post('/', createCertificateEmergencyUrssaf);
router.get('/', getAllCertificatesEmergencyUrssaf);
router.get('/:id', getCertificateEmergencyUrssafById);
router.get('/company/:companyId', getCertificateEmergencyUrssafByCompany);
router.get('/siren/:siren', getCertificateEmergencyUrssafBySIREN);
router.get('/siret/:siret', getCertificateEmergencyUrssafBySIRET);
router.put('/:id', updateCertificateEmergencyUrssaf);
router.delete('/:id', deleteCertificateEmergencyUrssaf);

export default router;
