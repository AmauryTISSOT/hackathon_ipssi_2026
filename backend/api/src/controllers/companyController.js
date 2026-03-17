import { Company } from '../models/Company.js';

export const createCompany = async (req, res) => {
  try {
    const company = new Company(req.body);
    await company.save();
    res.status(201).json(company);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

export const getAllCompanies = async (req, res) => {
  try {
    const { page = 1, limit = 10, country, owner } = req.query;
    const query = {};
    
    if (country) {
      query.country = country;
    }
    if (owner) {
      query.owner = { $regex: owner, $options: 'i' };
    }
    
    const companies = await Company.find(query)
      .limit(Number(limit))
      .skip((Number(page) - 1) * Number(limit))
      .sort({ createdAt: -1 });
    
    const total = await Company.countDocuments(query);
    
    res.json({
      companies,
      total,
      page: Number(page),
      totalPages: Math.ceil(total / Number(limit))
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

export const getCompanyById = async (req, res) => {
  try {
    const company = await Company.findById(req.params.id);
    if (!company) {
      res.status(404).json({ error: 'company not found' });
      return;
    }
    res.json(company);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

export const updateCompany = async (req, res) => {
  try {
    const company = await Company.findByIdAndUpdate(
      req.params.id,
      req.body,
      { new: true, runValidators: true }
    );
    
    if (!company) {
      res.status(404).json({ error: 'company not found' });
      return;
    }
    
    res.json(company);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

export const deleteCompany = async (req, res) => {
  try {
    const company = await Company.findByIdAndDelete(req.params.id);
    if (!company) {
      res.status(404).json({ error: 'company not found' });
      return;
    }
    res.json({ message: 'company deleted successfully' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};
