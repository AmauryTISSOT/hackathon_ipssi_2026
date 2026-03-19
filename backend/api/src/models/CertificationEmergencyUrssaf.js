import mongoose, { Schema } from "mongoose";

const CertificateEmergencyUrssafSchema = new Schema({
  siren: { type: Number },
  siret: { type: Number },
  social_security: { type: Number },
  internal_identifier: { type: Number },
  security_code: { type: String },
  created_at: { type: Date },
  place_at: { type: String },
  company_id: { type: Schema.Types.ObjectId, ref: 'Company' },
  source_filename: { type: String }
}, {
  timestamps: true
});

export const CertificateEmergencyUrssaf = mongoose.model('CertificateEmergencyUrssaf', CertificateEmergencyUrssafSchema);
