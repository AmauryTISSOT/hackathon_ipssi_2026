import mongoose from 'mongoose';
import logger from './logger.js';

export const connectDatabase = async () => {
  try {
    const mongoUri = process.env.MONGODB_URI;

    await mongoose.connect(mongoUri);

    logger.info('mongodb connected successfully');

    mongoose.set('debug', (coll, method, query, doc) => {
      logger.info({ coll, method, query, doc }, 'mongoose query');
    });

    mongoose.connection.on('error', (err) => {
      logger.error(err, 'mongodb connection error');
    });

    mongoose.connection.on('disconnected', () => {
      logger.warn('mongodb disconnected');
    });

  } catch (error) {
    logger.error(error, 'mongodb connection failed');
    process.exit(1);
  }
};
