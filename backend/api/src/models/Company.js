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
  nomenclature_activite_principale_unite_legale: { type: String },
  categorie_entreprise: { type: String },
  enseigne_etablissement: { type: String },
  sexe_unite_legale: { type: String, enum: ['M', 'F'] },
  nom_unite_legale: { type: String },
  nom_usage_unite_legale: { type: String },
  prenom_1_unite_legale: { type: String },
  prenom_usuel_unite_legale: { type: String },
  adresse_etablissement: { type: String },
  complement_adresse_etablissement: { type: String },
  numero_voie_etablissement: { type: String },
  indice_repetition_etablissement: { type: String },
  type_voie_etablissement: { type: String },
  libelle_voie_etablissement: { type: String },
  code_postal_etablissement: { type: String },
  libelle_commune_etablissement: { type: String },
  metadata: { type: {
    pipeline_processing_date: { type: Date },
    source: { type: String },
  }, default: {} },
}, {
  timestamps: true
});

export const Company = mongoose.model('Company', CompanySchema);
