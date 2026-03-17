import { KBIS } from '../models/KBIS.js';

export const createKBIS = async (req, res) => {
  try {
    const kbis = new KBIS(req.body);
    await kbis.save();
    res.status(201).json(kbis);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

export const getAllKBIS = async (req, res) => {
  try {
    const { page = 1, limit = 10, company_id } = req.query;
    const query = {};
    
    if (company_id) {
      query.company_id = company_id;
    }
    
    const kbis = await KBIS.find(query)
      .populate('company_id')
      .limit(Number(limit))
      .skip((Number(page) - 1) * Number(limit))
      .sort({ createdAt: -1 });
    
    const total = await KBIS.countDocuments(query);
    
    res.json({
      kbis,
      total,
      page: Number(page),
      totalPages: Math.ceil(total / Number(limit))
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

export const getKBISById = async (req, res) => {
  try {
    const kbis = await KBIS.findById(req.params.id).populate('company_id');
    if (!kbis) {
      res.status(404).json({ error: 'kbis not found' });
      return;
    }
    res.json(kbis);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

export const getKBISByCompany = async (req, res) => {
  try {
    const kbis = await KBIS.findOne({ company_id: req.params.companyId })
      .populate('company_id');
    if (!kbis) {
      res.status(404).json({ error: 'kbis not found for this company' });
      return;
    }
    res.json(kbis);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

export const updateKBIS = async (req, res) => {
  try {
    const kbis = await KBIS.findByIdAndUpdate(
      req.params.id,
      req.body,
      { new: true, runValidators: true }
    ).populate('company_id');
    
    if (!kbis) {
      res.status(404).json({ error: 'kbis not found' });
      return;
    }
    
    res.json(kbis);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

export const deleteKBIS = async (req, res) => {
  try {
    const kbis = await KBIS.findByIdAndDelete(req.params.id);
    if (!kbis) {
      res.status(404).json({ error: 'kbis not found' });
      return;
    }
    res.json({ message: 'kbis deleted successfully' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};
