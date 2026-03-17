import { Invoice } from '../models/Invoice.js';

export const createInvoice = async (req, res) => {
  try {
    const invoice = new Invoice(req.body);
    await invoice.save();
    res.status(201).json(invoice);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

export const getAllInvoices = async (req, res) => {
  try {
    const { page = 1, limit = 10, company_id, currency, language } = req.query;
    const query = {};
    
    if (company_id) {
      query.company_id = company_id;
    }
    if (currency) {
      query.currency = currency;
    }
    if (language) {
      query.language = language;
    }
    
    const invoices = await Invoice.find(query)
      .populate('company_id')
      .limit(Number(limit))
      .skip((Number(page) - 1) * Number(limit))
      .sort({ createdAt: -1 });
    
    const total = await Invoice.countDocuments(query);
    
    res.json({
      invoices,
      total,
      page: Number(page),
      totalPages: Math.ceil(total / Number(limit))
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

export const getInvoiceById = async (req, res) => {
  try {
    const invoice = await Invoice.findById(req.params.id).populate('company_id');
    if (!invoice) {
      res.status(404).json({ error: 'invoice not found' });
      return;
    }
    res.json(invoice);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

export const updateInvoice = async (req, res) => {
  try {
    const invoice = await Invoice.findByIdAndUpdate(
      req.params.id,
      req.body,
      { new: true, runValidators: true }
    ).populate('company_id');
    
    if (!invoice) {
      res.status(404).json({ error: 'invoice not found' });
      return;
    }
    
    res.json(invoice);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

export const deleteInvoice = async (req, res) => {
  try {
    const invoice = await Invoice.findByIdAndDelete(req.params.id);
    if (!invoice) {
      res.status(404).json({ error: 'invoice not found' });
      return;
    }
    res.json({ message: 'invoice deleted successfully' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

export const getInvoicesByCompany = async (req, res) => {
  try {
    const invoices = await Invoice.find({ company_id: req.params.companyId })
      .populate('company_id')
      .sort({ createdAt: -1 });
    res.json(invoices);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};
