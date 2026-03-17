import mongoose, { Schema } from 'mongoose';


const InvoiceLineSchema = new Schema({
  label: { type: String },
  vat_rate: { 
    type: String, 
    enum: ['FR_55', 'FR_100', 'FR_200', 'FR_1_75', 'FR_1_05', 'FR_21', 'FR_85'],
    required: true 
  },
  quantity: { type: Number },
  unit_price: { type: Number },
  discount: {
    type: {
      type: String,
      enum: ['relative', 'absolute']
    },
    value: { type: String }
  }
});

const InvoiceSchema = new Schema({
  currency: { 
    type: String, 
    enum: ['EUR', 'USD', 'GBP'],
    required: true,
    default: 'EUR'
  },
  language: { 
    type: String, 
    enum: ['fr', 'en', 'es'],
    required: true,
    default: 'fr'
  },
  invoice_lines: [InvoiceLineSchema],
  company_id: { type: Schema.Types.ObjectId, ref: 'Company' },
  issue_date: { type: Date },
  due_date: { type: Date },
  total_before_tax: { type: Number },
  total_tax: { type: Number },
  total: { type: Number }
}, {
  timestamps: true
});

export const Invoice = mongoose.model('Invoice', InvoiceSchema);
