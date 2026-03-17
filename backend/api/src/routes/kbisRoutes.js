import { Router } from 'express';
import {
  createKBIS,
  getAllKBIS,
  getKBISById,
  getKBISByCompany,
  updateKBIS,
  deleteKBIS
} from '../controllers/kbisController.js';

const router = Router();

router.post('/', createKBIS);
router.get('/', getAllKBIS);
router.get('/:id', getKBISById);
router.get('/company/:companyId', getKBISByCompany);
router.put('/:id', updateKBIS);
router.delete('/:id', deleteKBIS);

export default router;
