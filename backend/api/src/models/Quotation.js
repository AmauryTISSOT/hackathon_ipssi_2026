import mongoose, { Schema } from 'mongoose';

const QuotationLineSchema = new Schema({
  label: { type: String },
  vat_rate: { 
    type: String, 
    enum: ['FR_55', 'FR_100', 'FR_200', 'FR_1_75', 'FR_1_05', 'FR_21', 'FR_85'],
  },
  quantity: { type: Number },
  unit_price: { type: Number },
  quotation_id: { type: Schema.Types.ObjectId, ref: 'Quotation' }
});

const QuotationSchema = new Schema({
  label: { type: String },
  quotation_lines: [QuotationLineSchema],
  total_before_tax: { type: Number },
  total_tva: { type: Number },
  total: { type: Number },
  issuer: {
    name: { type: String },
    phone_number: { type: String },
    address: { type: String },
    email: { type: String },
    website: { type: String }
  },
  payment_terms: { type: String },
  additional_information: [{ type: String }],
  made_at: { type: String },
  issue_date: { type: Date },
  due_date: { type: Date },
  company_id: { type: Schema.Types.ObjectId, ref: 'Company' },
  source_filename: { type: String }
}, {
  timestamps: true
});

export const Quotation = mongoose.model('Quotation', QuotationSchema);
