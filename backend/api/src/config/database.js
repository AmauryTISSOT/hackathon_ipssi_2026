import mongoose from 'mongoose';

export const connectDatabase = async () => {
  try {
    const mongoUri = process.env.MONGODB_URI;
    
    await mongoose.connect(mongoUri);
    
    console.log('mongodb connected successfully');
    
    mongoose.connection.on('error', (err) => {
      console.error('mongodb connection error:', err);
    });
    
    mongoose.connection.on('disconnected', () => {
      console.warn('mongodb disconnected');
    });
    
  } catch (error) {
    console.error('mongodb connection failed:', error);
    process.exit(1);
  }
};
