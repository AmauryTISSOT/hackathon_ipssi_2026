import { CertificateEmergencyUrssaf } from '../models/CertificationEmergencyUrssaf.js';
import { removeMinioFiles } from '../services/documentService.js';

export const createCertificateEmergencyUrssaf = async (req, res) => {
  try {
    const certificate = new CertificateEmergencyUrssaf(req.body);
    await certificate.save();
    res.status(201).json(certificate);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

export const getAllCertificatesEmergencyUrssaf = async (req, res) => {
  try {
    const { page = 1, limit = 10, company_id, siren, siret } = req.query;
    const query = {};
    
    if (company_id) {
      query.company_id = company_id;
    }
    if (siren) {
      query.siren = Number(siren);
    }
    if (siret) {
      query.siret = Number(siret);
    }
    
    const certificates = await CertificateEmergencyUrssaf.find(query)
      .populate('company_id')
      .limit(Number(limit))
      .skip((Number(page) - 1) * Number(limit))
      .sort({ createdAt: -1 });
    
    const total = await CertificateEmergencyUrssaf.countDocuments(query);
    
    res.json({
      certificates,
      total,
      page: Number(page),
      totalPages: Math.ceil(total / Number(limit))
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

export const getCertificateEmergencyUrssafById = async (req, res) => {
  try {
    const certificate = await CertificateEmergencyUrssaf.findById(req.params.id).populate('company_id');
    if (!certificate) {
      res.status(404).json({ error: 'certificate emergency urssaf not found' });
      return;
    }
    res.json(certificate);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

export const getCertificateEmergencyUrssafByCompany = async (req, res) => {
  try {
    const certificates = await CertificateEmergencyUrssaf.find({ company_id: req.params.companyId })
      .populate('company_id')
      .sort({ createdAt: -1 });
    res.json(certificates);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

export const getCertificateEmergencyUrssafBySIREN = async (req, res) => {
  try {
    const certificate = await CertificateEmergencyUrssaf.findOne({ siren: Number(req.params.siren) })
      .populate('company_id');
    
    if (!certificate) {
      res.status(404).json({ error: 'certificate emergency urssaf not found for this siren' });
      return;
    }
    res.json(certificate);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

export const getCertificateEmergencyUrssafBySIRET = async (req, res) => {
  try {
    const certificate = await CertificateEmergencyUrssaf.findOne({ siret: Number(req.params.siret) })
      .populate('company_id');
    
    if (!certificate) {
      res.status(404).json({ error: 'certificate emergency urssaf not found for this siret' });
      return;
    }
    res.json(certificate);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

export const updateCertificateEmergencyUrssaf = async (req, res) => {
  try {
    const certificate = await CertificateEmergencyUrssaf.findByIdAndUpdate(
      req.params.id,
      req.body,
      { new: true, runValidators: true }
    ).populate('company_id');
    
    if (!certificate) {
      res.status(404).json({ error: 'certificate emergency urssaf not found' });
      return;
    }
    
    res.json(certificate);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

export const deleteCertificateEmergencyUrssaf = async (req, res) => {
  try {
    const certificate = await CertificateEmergencyUrssaf.findByIdAndDelete(req.params.id);
    if (!certificate) {
      res.status(404).json({ error: 'certificate emergency urssaf not found' });
      return;
    }
    if (certificate.source_filename) {
      await removeMinioFiles(certificate.source_filename);
    }
    res.json({ message: 'certificate emergency urssaf deleted successfully' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};
