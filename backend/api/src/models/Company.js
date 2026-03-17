import mongoose, { Schema } from 'mongoose';

const CompanySchema = new Schema({
  siren: { type: String },
  nic: { type: String },
  siret: { type: String },
  date_creation_etablissement: { type: Date },
  etablissement_siege: { type: Boolean },
  etat_administratif_unite_legale: { type: String },
  date_creation_unite_legale: { type: Date },
  denomination_unite_legale: { type: String },
  activite_principale_unite_legale: { type: String },
  nomenclatureActivitePrincipaleUniteLegale: { type: String },
  categorieEntreprise: { type: String },
  adresseEtablissement: { type: String },
  complementAdresseEtablissement: { type: String },
  numeroVoieEtablissement: { type: String },
  indiceRepetitionEtablissement: { type: String },
  typeVoieEtablissement: { type: String },
  libelleVoieEtablissement: { type: String },
  codePostalEtablissement: { type: String },
  libelleCommuneEtablissement: { type: String },
  metadata: { type: Object, default: {} },
  owner: { type: String },
  country: { 
    type: String, 
    enum: ['FR', 'US', 'UK', 'ES', 'DE'],
    default: 'FR'
  },
}, {
  timestamps: true
});

export const Company = mongoose.model('Company', CompanySchema);
