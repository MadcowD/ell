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
import { useZoomPanHelper } from 'react-flow-renderer';
import { ZoomIn, ZoomOut, Lock, Maximize, Unlock } from 'lucide-react';
import { Button } from "components/common/Button";

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
    <div className="h-full relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
      >
        <Panel>
        </Panel>
        <Background />
        <CustomControls />
      </ReactFlow>
    </div>
  );
};

function CustomControls() {
  const { zoomIn, zoomOut, fitView, setNodes } = useReactFlow();
  const [nodesLocked, setNodesLocked] = useState(false);

  const handleZoomIn = () => zoomIn({ duration: 300, step: 0.5 });
  const handleZoomOut = () => zoomOut({ duration: 300, step: 0.5 });
  const handleFitView = () => fitView({ duration: 500, padding: 0.1 });
  const handleToggleNodeLock = () => {
    setNodes((nodes) =>
      nodes.map((node) => ({ ...node, draggable: nodesLocked }))
    );
    setNodesLocked(!nodesLocked);
  };

  return (
    <div className="absolute bottom-10 left-1/2 transform -translate-x-1/2 flex space-x-2 z-10">
      <Button onClick={handleZoomIn} variant="secondary" size="sm">
        <ZoomIn className="w-4 h-4 mr-2" />
        Zoom In
      </Button>
      <Button onClick={handleZoomOut} variant="secondary" size="sm">
        <ZoomOut className="w-4 h-4 mr-2" />
        Zoom Out
      </Button>
      <Button onClick={handleFitView} variant="secondary" size="sm">
        <Maximize className="w-4 h-4 mr-2" />
        Fit View
      </Button>
      <Button onClick={handleToggleNodeLock} variant="secondary" size="sm">
        {nodesLocked ? <Unlock className="w-4 h-4 mr-2" /> : <Lock className="w-4 h-4 mr-2" />}
        {nodesLocked ? 'Unlock Nodes' : 'Lock Nodes'}
      </Button>
    </div>
  );
}

export function DependencyGraph({ lmps, traces, ...rest }) {
  // construct ndoes from LMPS
  const { initialEdges, initialNodes } = useMemo(
    () => getInitialGraph(lmps, traces),
    [lmps, traces]
  );

  return (
    <div
      className="h-full w-full border-gray-700"
      {...rest}
    >
      <ReactFlowProvider>
        <LayoutFlow initialEdges={initialEdges} initialNodes={initialNodes} />
      </ReactFlowProvider>
    </div>
  );
}