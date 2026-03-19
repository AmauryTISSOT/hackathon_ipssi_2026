import jwt from 'jsonwebtoken';
import User from '../models/User.js';

export const protect = async (req, res, next) => {
  try {
    const authHeader = req.headers.authorization;
    let token = null;

    if (authHeader && authHeader.startsWith('Bearer ')) {
      token = authHeader.split(' ')[1];
    } else if (req.query.token) {
      token = req.query.token;
    }

    if (!token) {
      return res.status(401).json({ message: 'Token manquant ou invalide' });
    }
    const decoded = jwt.verify(token, process.env.JWT_SECRET);

    const user = await User.findById(decoded.id).select('-password');
    if (!user) return res.status(401).json({ message: 'Utilisateur introuvable' });

    req.user = user;
    next();
  } catch (error) {
    res.status(401).json({ message: 'Token invalide ou expiré' });
  }
};

export const checkRole = (...roles) => (req, res, next) => {
  if (!req.user) {
    return res.status(401).json({ message: 'Non authentifié' });
  }
  if (!roles.includes(req.user.role)) {
    return res.status(403).json({ message: 'Accès refusé : rôle insuffisant' });
  }
  next();
};
