import React from 'react';
import { FiClock, FiZap, FiHash, FiBox, FiTag, FiLayers } from 'react-icons/fi';
import { motion } from 'framer-motion';
import { Card } from '../common/Card';

export function InvocationInfoPane({ invocation, isFullWidth }) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className={`w-full bg-card p-4 text-sm h-full`}
      >
        <div className="space-y-2 h-full">
          <h3 className="text-sm font-semibold text-card-foreground mb-1">Invocation Details</h3>
          <div className="grid grid-cols-2 gap-y-0.5">
            <div className="flex items-center">
              <FiClock className="mr-1 text-muted-foreground" size={12} />
              <span className="text-muted-foreground">Created At:</span>
            </div>
            <div className="text-right text-gray-300">{new Date(invocation.created_at).toLocaleTimeString()}</div>

            <div className="flex items-center">
              <FiZap className="mr-1 text-muted-foreground" size={12} />
              <span className="text-muted-foreground">Latency:</span>
            </div>
            <div className="text-right text-gray-300">{(invocation.latency_ms / 1000).toFixed(2)}s</div>

            <div className="flex items-center">
              <FiHash className="mr-1 text-muted-foreground" size={12} />
              <span className="text-muted-foreground">Prompt Tokens:</span>
            </div>
            <div className="text-right text-gray-300">{invocation.prompt_tokens || "N/A"}</div>

            <div className="flex items-center">
              <FiBox className="mr-1 text-muted-foreground" size={12} />
              <span className="text-muted-foreground">Completion Tokens:</span>
            </div>
            <div className="text-right text-gray-300">{invocation.completion_tokens || "N/A"}</div>

            <div className="flex items-center">
              <FiTag className="mr-1 text-muted-foreground" size={12} />
              <span className="text-muted-foreground">LMP Type:</span>
            </div>
            <div className="text-right">
              <span className="text-gray-300 bg-blue-900 inline-block px-2 py-0.5 rounded text-xs">
                {invocation.lmp?.is_lm ? "LM" : "LMP"}
              </span>
            </div>

          </div>
        </div>
      </motion.div>
    );
}