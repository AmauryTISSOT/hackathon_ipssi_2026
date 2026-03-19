import Anomaly from '../models/Anomaly.js';
import Document from '../models/Document.js';

export const createAnomaly = async (anomalyData) => {
  const anomaly = await Anomaly.create(anomalyData);
  return anomaly;
};

export const createAnomaliesFromAlerts = async (documentId, alerts) => {
  if (!alerts || alerts.length === 0) {
    return [];
  }

  const anomalies = alerts.map(alert => ({
    document_id: documentId,
    anomaly_type: alert.type,
    control: alert.control,
  }));

  const createdAnomalies = await Anomaly.insertMany(anomalies);
  return createdAnomalies;
};

export const getAnomaliesByDocument = async (documentId) => {
  const anomalies = await Anomaly.find({ document_id: documentId })
    .populate('resolved_by', 'email')
    .sort({ createdAt: -1 });
  return anomalies;
};

export const getAllAnomalies = async (filters = {}) => {
  const query = {};

  if (filters.status) {
    query.status = filters.status;
  }

  if (filters.anomaly_type) {
    query.anomaly_type = filters.anomaly_type;
  }

  const anomalies = await Anomaly.find(query)
    .populate('document_id', 'filename doc_type')
    .populate('resolved_by', 'email')
    .sort({ createdAt: -1 });

  return anomalies;
};

export const getAnomalyById = async (anomalyId) => {
  const anomaly = await Anomaly.findById(anomalyId)
    .populate('document_id', 'filename doc_type')
    .populate('resolved_by', 'email');

  if (!anomaly) {
    throw new Error('Anomalie non trouvée');
  }

  return anomaly;
};

export const updateAnomalyStatus = async (anomalyId, status, userId, resolutionNote) => {
  const anomaly = await Anomaly.findById(anomalyId);

  if (!anomaly) {
    throw new Error('Anomalie non trouvée');
  }

  anomaly.status = status;

  if (status === 'resolved') {
    anomaly.resolved_by = userId;
    anomaly.resolved_at = new Date();
    if (resolutionNote) {
      anomaly.resolution_note = resolutionNote;
    }
  }

  await anomaly.save();
  return anomaly;
};

export const deleteAnomaly = async (anomalyId) => {
  const anomaly = await Anomaly.findByIdAndDelete(anomalyId);

  if (!anomaly) {
    throw new Error('Anomalie non trouvée');
  }

  return anomaly;
};

export const getAnomalyStats = async () => {
  const stats = await Anomaly.aggregate([
    {
      $group: {
        _id: '$status',
        count: { $sum: 1 },
      },
    },
  ]);

  const typeStats = await Anomaly.aggregate([
    {
      $group: {
        _id: '$anomaly_type',
        count: { $sum: 1 },
      },
    },
  ]);

  return {
    byStatus: stats.reduce((acc, item) => {
      acc[item._id] = item.count;
      return acc;
    }, {}),
    byType: typeStats.reduce((acc, item) => {
      acc[item._id] = item.count;
      return acc;
    }, {}),
  };
};
