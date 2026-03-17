import { Router } from 'express';
import {
  createQuotation,
  getAllQuotations,
  getQuotationById,
  updateQuotation,
  deleteQuotation,
  getQuotationsByCompany
} from '../controllers/quotationController.js';

const router = Router();

router.post('/', createQuotation);
router.get('/', getAllQuotations);
router.get('/:id', getQuotationById);
router.get('/company/:companyId', getQuotationsByCompany);
router.put('/:id', updateQuotation);
router.delete('/:id', deleteQuotation);

export default router;
