import * as anomalyService from '../services/anomalyService.js';

export const createAnomaly = async (req, res) => {
  try {
    const anomaly = await anomalyService.createAnomaly(req.body);
    res.status(201).json(anomaly);
  } catch (error) {
    res.status(400).json({ message: error.message });
  }
};

export const getAnomaliesByDocument = async (req, res) => {
  try {
    const { documentId } = req.params;
    const anomalies = await anomalyService.getAnomaliesByDocument(documentId);
    res.status(200).json(anomalies);
  } catch (error) {
    res.status(400).json({ message: error.message });
  }
};

export const getAllAnomalies = async (req, res) => {
  try {
    const filters = {
      status: req.query.status,
      anomaly_type: req.query.anomaly_type,
    };
    const anomalies = await anomalyService.getAllAnomalies(filters);
    res.status(200).json(anomalies);
  } catch (error) {
    res.status(400).json({ message: error.message });
  }
};

export const getAnomalyById = async (req, res) => {
  try {
    const { id } = req.params;
    const anomaly = await anomalyService.getAnomalyById(id);
    res.status(200).json(anomaly);
  } catch (error) {
    res.status(404).json({ message: error.message });
  }
};

export const updateAnomalyStatus = async (req, res) => {
  try {
    const { id } = req.params;
    const { status, resolution_note } = req.body;
    const userId = req.user?.id;

    const anomaly = await anomalyService.updateAnomalyStatus(
      id,
      status,
      userId,
      resolution_note
    );

    res.status(200).json(anomaly);
  } catch (error) {
    res.status(400).json({ message: error.message });
  }
};

export const deleteAnomaly = async (req, res) => {
  try {
    const { id } = req.params;
    await anomalyService.deleteAnomaly(id);
    res.status(200).json({ message: 'Anomalie supprimée avec succès' });
  } catch (error) {
    res.status(404).json({ message: error.message });
  }
};

export const getAnomalyStats = async (req, res) => {
  try {
    const stats = await anomalyService.getAnomalyStats();
    res.status(200).json(stats);
  } catch (error) {
    res.status(400).json({ message: error.message });
  }
};
