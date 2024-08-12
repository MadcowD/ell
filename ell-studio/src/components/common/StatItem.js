import React from 'react';
import { motion } from 'framer-motion';

const StatItem = ({ icon: Icon, label, value }) => (
  <motion.div 
    whileHover={{ scale: 1.05 }}
    className="flex items-center justify-between text-sm py-2 border-b border-gray-700 last:border-b-0"
  >
    <span className="flex items-center text-gray-400">
      <Icon className="mr-2" size={14} />
      {label}
    </span>
    <span className="font-medium text-gray-200">{value}</span>
  </motion.div>
);

export default StatItem;