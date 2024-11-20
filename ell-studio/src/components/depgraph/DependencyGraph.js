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
import { LMPCardTitle } from "./LMPCardTitle";
import { OldCard } from "../OldCard";
import EvaluationCard from "../evaluations/EvaluationCard"; // Update this import
import "reactflow/dist/style.css";
import { ZoomIn, ZoomOut, Lock, Maximize, Unlock } from 'lucide-react';
import { Button } from "components/common/Button";

import { getInitialGraph } from "./graphUtils";
import { useLayoutedElements } from "./layoutUtils";


function LMPNode({ data }) {
  const { lmp } = data;
  const onChange = useCallback((evt) => {}, []);

  return (
    <>
      <Handle type="source" position={Position.Bottom} id="uses" />
      <OldCard  key={lmp.lmp_id}>
        <Link to={`/lmp/${lmp.name}`}>
          <LMPCardTitle displayVersion lmp={lmp} fontSize="sm" />
        </Link>
      </OldCard>
      <Handle type="target" position={Position.Top} id="usedby" />
      <Handle type="target" position={Position.Left} id="inputs" />
      <Handle type="source" position={Position.Right} id="outputs" />
    </>
  );
}
function EvalNode({ data }) {
  const { evaluation } = data;

  return (
    <>
      <Handle type="source" position={Position.Bottom} id="uses" />
      <div className="w-[400px]"> {/* Adjust the width as needed */}
        <EvaluationCard evaluation={evaluation} isGraphMode={true} />
      </div>
      <Handle type="target" position={Position.Top} id="usedby" />
      <Handle type="target" position={Position.Left} id="inputs" />
      <Handle type="source" position={Position.Right} id="outputs" />
    </>
  );
}

const LayoutFlow = ({ initialNodes, initialEdges }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [initialised, { toggle, isRunning }] = useLayoutedElements();
  const [didInitialSimulation, setDidInitialSimulation] = useState(false);
  const { fitView } = useReactFlow();

  // Start the simulation automatically when initialized and run it for 1 second
  useEffect(() => {
    if (initialised && !didInitialSimulation) {
      setDidInitialSimulation(true);
      // toggle();

    fitView({ duration: 500, padding: 0.1 });
      setTimeout(() => {
        // toggle();
        // Fit view after the simulation has run
        fitView({ duration: 500, padding: 0.1 });
      }, 1000);
    }
  }, [initialised, didInitialSimulation, toggle, fitView]);

  const nodeTypes = useMemo(() => ({ 
    lmp: LMPNode,
    evaluation: EvalNode // Add the new EvalNode type
  }), []);

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
    <div className="absolute top-4 left-4 flex space-x-2 z-10">
      <Button onClick={handleZoomIn} variant="secondary" size="sm">
        <ZoomIn className="w-4 h-4" />
      </Button>
      <Button onClick={handleZoomOut} variant="secondary" size="sm">
        <ZoomOut className="w-4 h-4" />
      </Button>
      <Button onClick={handleFitView} variant="secondary" size="sm">
        <Maximize className="w-4 h-4" />
      </Button>
      <Button onClick={handleToggleNodeLock} variant="secondary" size="sm">
        {nodesLocked ? <Lock className="w-4 h-4" /> : <Unlock className="w-4 h-4" />}
      </Button>
    </div>
  );
}

export function DependencyGraph({ lmps, traces, evals, ...rest }) {
  // construct ndoes from LMPS
  const { initialEdges, initialNodes } = useMemo(
    () => getInitialGraph(lmps, traces, evals),
    [lmps, traces, evals]
  );

  return (
    <div
      className="h-full h-full w-full border-gray-700"
      {...rest}
    >
      <ReactFlowProvider>
        <LayoutFlow initialEdges={initialEdges} initialNodes={initialNodes} />
      </ReactFlowProvider>
    </div>
  );
}
