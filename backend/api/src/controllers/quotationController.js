import { Quotation } from '../models/Quotation.js';

export const createQuotation = async (req, res) => {
  try {
    const quotation = new Quotation(req.body);
    await quotation.save();
    res.status(201).json(quotation);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

export const getAllQuotations = async (req, res) => {
  try {
    const { page = 1, limit = 10, company_id } = req.query;
    const query = {};
    
    if (company_id) {
      query.company_id = company_id;
    }
    
    const quotations = await Quotation.find(query)
      .populate('company_id')
      .limit(Number(limit))
      .skip((Number(page) - 1) * Number(limit))
      .sort({ createdAt: -1 });
    
    const total = await Quotation.countDocuments(query);
    
    res.json({
      quotations,
      total,
      page: Number(page),
      totalPages: Math.ceil(total / Number(limit))
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

export const getQuotationById = async (req, res) => {
  try {
    const quotation = await Quotation.findById(req.params.id).populate('company_id');
    if (!quotation) {
      res.status(404).json({ error: 'quotation not found' });
      return;
    }
    res.json(quotation);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

export const updateQuotation = async (req, res) => {
  try {
    const quotation = await Quotation.findByIdAndUpdate(
      req.params.id,
      req.body,
      { new: true, runValidators: true }
    ).populate('company_id');
    
    if (!quotation) {
      res.status(404).json({ error: 'quotation not found' });
      return;
    }
    
    res.json(quotation);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

export const deleteQuotation = async (req, res) => {
  try {
    const quotation = await Quotation.findByIdAndDelete(req.params.id);
    if (!quotation) {
      res.status(404).json({ error: 'quotation not found' });
      return;
    }
    res.json({ message: 'quotation deleted successfully' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

export const getQuotationsByCompany = async (req, res) => {
  try {
    const quotations = await Quotation.find({ company_id: req.params.companyId })
      .populate('company_id')
      .sort({ createdAt: -1 });
    res.json(quotations);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};
