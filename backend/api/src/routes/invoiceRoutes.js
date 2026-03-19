import { Router } from 'express';
import {
  createInvoice,
  getAllInvoices,
  getInvoiceById,
  updateInvoice,
  deleteInvoice,
  getInvoicesByCompany
} from '../controllers/invoiceController.js';

const router = Router();

router.post('/', createInvoice);
router.get('/', getAllInvoices);
router.get('/:id', getInvoiceById);
router.get('/company/:companyId', getInvoicesByCompany);
router.put('/:id', updateInvoice);
router.delete('/:id', deleteInvoice);

export default router;
