import mongoose from 'mongoose';

const userSchema = new mongoose.Schema(
  {
    email: {
      type: String,
      required: true,
      unique: true,
      lowercase: true,
      trim: true,
    },
    password: {
      type: String,
      required: true,
    },
    role: {
      type: String,
      enum: ['user', 'comptable'], // seules ces deux valeurs sont acceptées
      default: 'user',             // par défaut, tout nouvel inscrit est un utilisateur normal
    },
  },
  {
    timestamps: true,
  }
);

export default mongoose.model('User', userSchema);
