import { RIB } from '../models/RIB.js';

export const createRIB = async (req, res) => {
  try {
    const rib = new RIB(req.body);
    await rib.save();
    res.status(201).json(rib);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

export const getAllRIBs = async (req, res) => {
  try {
    const { page = 1, limit = 10, company_id } = req.query;
    const query = {};
    
    if (company_id) {
      query.company_id = company_id;
    }
    
    const ribs = await RIB.find(query)
      .populate('company_id')
      .limit(Number(limit))
      .skip((Number(page) - 1) * Number(limit))
      .sort({ createdAt: -1 });
    
    const total = await RIB.countDocuments(query);
    
    res.json({
      ribs,
      total,
      page: Number(page),
      totalPages: Math.ceil(total / Number(limit))
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

export const getRIBById = async (req, res) => {
  try {
    const rib = await RIB.findById(req.params.id).populate('company_id');
    if (!rib) {
      res.status(404).json({ error: 'rib not found' });
      return;
    }
    res.json(rib);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

export const getRIBByCompany = async (req, res) => {
  try {
    const ribs = await RIB.find({ company_id: req.params.companyId })
      .populate('company_id')
      .sort({ createdAt: -1 });
    res.json(ribs);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

export const updateRIB = async (req, res) => {
  try {
    const rib = await RIB.findByIdAndUpdate(
      req.params.id,
      req.body,
      { new: true, runValidators: true }
    ).populate('company_id');
    
    if (!rib) {
      res.status(404).json({ error: 'rib not found' });
      return;
    }
    
    res.json(rib);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

export const deleteRIB = async (req, res) => {
  try {
    const rib = await RIB.findByIdAndDelete(req.params.id);
    if (!rib) {
      res.status(404).json({ error: 'rib not found' });
      return;
    }
    res.json({ message: 'rib deleted successfully' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};
