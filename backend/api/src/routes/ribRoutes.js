import { Router } from 'express';
import {
  createRIB,
  getAllRIBs,
  getRIBById,
  getRIBByCompany,
  updateRIB,
  deleteRIB
} from '../controllers/ribController.js';

const router = Router();

router.post('/', createRIB);
router.get('/', getAllRIBs);
router.get('/:id', getRIBById);
router.get('/company/:companyId', getRIBByCompany);
router.put('/:id', updateRIB);
router.delete('/:id', deleteRIB);

export default router;
