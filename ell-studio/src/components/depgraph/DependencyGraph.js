import React, {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import ReactFlow, {
  Panel,
  useNodesState,
  useEdgesState,
  useReactFlow,
  Background,
  Controls,
  Handle,
  Position,
  ReactFlowProvider,
} from "reactflow";
import { getBezierPath } from 'reactflow';


import { Link } from "react-router-dom";
import { LMPCardTitle } from "./LMPCardTitle"; // Add this import

import { Card } from "../Card";
import "reactflow/dist/style.css";


import { useLayoutedElements, getInitialGraph } from "./graphUtils";


function LMPNode({ data }) {
  const { lmp } = data;
  const onChange = useCallback((evt) => {}, []);

  return (
    <>
      <Handle type="source" position={Position.Top} />
      <Card  key={lmp.lmp_id}>
        <Link to={`/lmp/${lmp.name}`}>
          <LMPCardTitle displayVersion lmp={lmp} fontSize="sm" />
        </Link>
      </Card>
      <Handle type="target" position={Position.Bottom} id="a" />
      <Handle type="target" position={Position.Left} id="inputs" />
      <Handle type="source" position={Position.Right} id="outputs" />
    </>
  );
}


const LayoutFlow = ({ initialNodes, initialEdges }) => {
  const [nodes, _, onNodesChange] = useNodesState(initialNodes);
  const [edges, __, onEdgesChange] = useEdgesState(initialEdges);
  const [initialised, { toggle, isRunning }] = useLayoutedElements();
  const [didInitialSimulation, setDidInitialSimulation] = useState(false);

  // Start the simulation automatically when the initialized is good & run it for like 1second
  useEffect(() => {
    if (initialised && !didInitialSimulation) {
      setDidInitialSimulation(true);
      toggle();
      setTimeout(() => {
        toggle();
      }, 1000);
    }
  }, [initialised, didInitialSimulation]);

  const nodeTypes = useMemo(() => ({ lmp: LMPNode }), []);

  return (
    
    <div style={{ height: 600 }}>
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      nodeTypes={nodeTypes}
      // fitView
    >
      <Panel>
      </Panel>
      <Controls />

      <Background />
    </ReactFlow>
    </div>
  );
};


export function DependencyGraph({ lmps, traces, ...rest }) {
  // construct ndoes from LMPS
  const { initialEdges, initialNodes } = useMemo(
    () => getInitialGraph(lmps, traces),
    [lmps, traces]
  );

  return (
    <div
      className="h-600px w-full rounded-lg border border-gray-700"
      {...rest}
    >
      <ReactFlowProvider>
        <LayoutFlow initialEdges={initialEdges} initialNodes={initialNodes} />
      </ReactFlowProvider>
    </div>
  );
}