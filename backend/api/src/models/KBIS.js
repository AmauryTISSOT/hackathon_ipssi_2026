import mongoose, { Schema } from 'mongoose';

const LegalEntitySchema = new Schema({
  registration_rcs: { type: String, required: true },
  date_registration: { type: Date, required: true },
  corporate_name: { type: String, required: true },
  legal_form: { type: String, required: true },
  share_capital: { type: Number, required: true },
  registered_address: { type: String, required: true },
  main_activities: { type: String, required: true },
  duration_legal_entity: { type: Date, required: true },
  financial_year_closing_date: { type: String, required: true }
});

const ManagementSchema = new Schema({
  category: { 
    type: String, 
    enum: ['manager', 'partner', 'member', 'control', 'director'],
    required: true 
  },
  first_name: { type: String, required: true },
  last_name: { type: String, required: true },
  birthdate: { type: Date, required: true },
  place_of_birth: { type: String, required: true },
  nationality: { type: String, required: true },
  private_address: { type: String, required: true }
});

const InformationRelatingActivityMainEstablishmentSchema = new Schema({
  establishment_address: { type: String, required: true },
  trading_name: { type: String, required: true },
  activity: { type: String, required: true },
  commencement_activity: { type: Date, required: true },
  origin_business: { type: String, required: true },
  method_operation: { type: String, required: true }
});

const InformationRelatingAnotherEstablishmentJurisdictionSchema = new Schema({
  establishment_address: { type: String, required: true },
  activity: { type: String, required: true },
  commencement_activity: { type: Date, required: true },
  origin_business: { type: String, required: true },
  method_operation: { type: String, required: true }
});

const KBISSchema = new Schema({
  legal_entity: { type: LegalEntitySchema, required: true },
  management: [ManagementSchema],
  information_relating_activity_main_establishment: { 
    type: InformationRelatingActivityMainEstablishmentSchema, 
    required: true 
  },
  information_relating_another_establishment_jurisdiction: { 
    type: InformationRelatingAnotherEstablishmentJurisdictionSchema, 
    required: true 
  },
  company_id: { type: Schema.Types.ObjectId, ref: 'Company', required: true }
}, {
  timestamps: true
});

export const KBIS = mongoose.model('KBIS', KBISSchema);
