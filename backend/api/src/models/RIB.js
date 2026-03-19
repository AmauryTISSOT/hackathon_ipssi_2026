import mongoose, { Schema } from 'mongoose';

const RIBSchema = new Schema({
  iban: { type: String },
  bic: { type: String },
  bank_code: { type: String },
  agency_code: { type: String },
  account_number: { type: String },
  key: { type: Number },
  registered_address: { type: String },
  company_id: { type: Schema.Types.ObjectId, ref: 'Company' },
  source_filename: { type: String }
}, {
  timestamps: true
});

export const RIB = mongoose.model('RIB', RIBSchema);
