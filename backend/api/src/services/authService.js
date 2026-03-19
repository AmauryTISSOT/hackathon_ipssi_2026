import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import User from '../models/User.js';

const generateToken = (userId) => {
  return jwt.sign(
    { id: userId },
    process.env.JWT_SECRET,
    { expiresIn: process.env.JWT_EXPIRES_IN }
  );
};

export const register = async ({ email, password, role }) => {
  const existingUser = await User.findOne({ email });
  if (existingUser) throw new Error('Email déjà utilisé');

  const hashedPassword = await bcrypt.hash(password, 10);
  
  const userData = { email, password: hashedPassword };
  if (role) {
    userData.role = role;
  }
  
  const user = await User.create(userData);

  const token = generateToken(user._id);

  return { user: { id: user._id, email: user.email, role: user.role }, token };
};

export const login = async ({ email, password }) => {
  const user = await User.findOne({ email });
  if (!user) throw new Error('Email ou mot de passe incorrect');

  const isMatch = await bcrypt.compare(password, user.password);
  if (!isMatch) throw new Error('Email ou mot de passe incorrect');

  const token = generateToken(user._id);

  return { user: { id: user._id, email: user.email, role: user.role }, token };
};
