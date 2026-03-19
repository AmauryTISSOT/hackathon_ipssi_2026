import mongoose from 'mongoose';

const documentSchema = new mongoose.Schema(
  {
    filename: {
      type: String,
      required: true,
    },
    doc_type: {
      type: String,
      default: null,
    },
    status: {
      type: String,
      enum: ['pending', 'processed', 'failed'],
      default: 'pending',
    },
    user_id: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User',
      required: true,
    },
    dag_run_id: {
      type: String,
    },
  },
  {
    timestamps: true,
  }
);

export default mongoose.model('Document', documentSchema);
