import mongoose from 'mongoose';

const anomalySchema = new mongoose.Schema(
  {
    document_id: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'Document',
      required: true,
    },
    anomaly_type: {
      type: String,
      enum: [
        'iban_invalid',
        'tva_number_invalid',
        'tva_mismatch',
        'line_price_mismatch',
        'siret_invalid',
        'siret_format',
        'invoice_dates_invalid',
        'date_future',
        'missing_amounts',
        'siren_siret_inconsistency',
        'company_closed',
        'company_name_mismatch_api',
        'missing_siret',
        'missing_siren',
        'missing_siret_and_siren',
        'siret_api_invalid',
        'siret_format_invalid'
      ],
      required: true,
    },
    control: {
      type: String,
    },
    status: {
      type: String,
      enum: ['pending', 'resolved', 'ignored'],
      default: 'pending',
    },
    resolved_by: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User',
    },
    resolved_at: {
      type: Date,
    },
    resolution_note: {
      type: String,
    },
  },
  {
    timestamps: true,
  }
);

anomalySchema.index({ document_id: 1 });
anomalySchema.index({ status: 1 });
anomalySchema.index({ anomaly_type: 1 });

export default mongoose.model('Anomaly', anomalySchema);
