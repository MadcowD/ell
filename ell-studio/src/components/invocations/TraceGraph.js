import React, { useState, useMemo } from 'react';
import { FiChevronDown, FiChevronRight, FiZap } from 'react-icons/fi';
import { LMPCardTitle } from '../depgraph/LMPCardTitle';
import { useEffect } from 'react';
import axios from 'axios';


const API_BASE_URL = "http://localhost:8080"

const TraceNode = ({ node, depth = 0, isLast = false }) => {
  const [expanded, setExpanded] = useState(depth < 1);
  const gradientColor = useMemo(() => `hsl(${200 - depth * 15}, 85%, ${70 - depth * 5}%)`, [depth]);

  return (
    <div className={`relative ${!isLast ? 'mb-2' : ''}`}>
      <div className={`flex items-center space-x-2 py-1 px-1 rounded hover:bg-gray-800 cursor-pointer text-sm transition-all duration-150 ease-in-out
        ${node.isHighlighted ? 'bg-yellow-500 bg-opacity-20 border border-yellow-500' : ''}`} onClick={() => setExpanded(!expanded)}>
        <span className="text-gray-400 w-4 flex-shrink-0" style={{ marginLeft: `${depth * 16}px` }}>
          {node.children?.length > 0 ? (
            expanded ? <FiChevronDown size={12} /> : <FiChevronRight size={12} />
          ) : <FiZap size={10} className="ml-0.5" />}
        </span>
        <LMPCardTitle  fontSize="xs" padding={false} lmp={{name: node.name, is_lmp : false}} />
        
        <span className="text-gray-300 px-1  text-xs whitespace-nowrap">
          {node.duration.toFixed(2)}ms
        </span>
        {node.isHighlighted && (
          <span className="text-yellow-500 text-xs ml-2">Highlighted</span>
        )}
      </div>
      {expanded && node.children && (
        <div className="mt-1">
          {node.children.map((child, index) => (
            <TraceNode 
              key={index} 
              node={child} 
              depth={depth + 1} 
              isLast={index === node.children.length - 1}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export const TraceGraph = ({ from }) => {
    const [traceData, setTraceData] = useState({
        name: "",
        icon: "",
        duration: 0,
        tokens: 0,
        tag: "",
        children: []
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchTraceData = async () => {
            try {
                const response = await axios.get(`${API_BASE_URL}/api/traces/${from.id}`);
                const traces = response.data;

                const formatTraceData = (trace) => {
                    return {
                        name: trace.consumed_lmp.name,
                        duration: trace.consumed.latency_ms,
                        tokens: trace.consumed.prompt_tokens + trace.consumed.completion_tokens,
                        tag: trace.consumed.lmp_id,
                        invocation_id: trace.consumed.invocation_id,
                        // Ignoring children for now
                    };
                };

                const formattedTraceData = traces.map(trace => formatTraceData(trace));
                
                setTraceData(formattedTraceData);
            } catch (error) {
                console.error('Error fetching trace data:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchTraceData();
    }, [from]);

  return (
    <div className="bg-gray-900 p-2 rounded-lg shadow-xl text-sm overflow-x-hidden">
      {loading ? (
        <div className="text-gray-400 text-center">Loading...</div>
      ) : (
        traceData?.map((child, index) => (
          <TraceNode 
            key={index}
            node={child} 
            isLast={index === traceData.length - 1}
          />
        ))
      )}
    </div>
  );
};