import { useMemo } from "react";
import ReactFlow, {
  useReactFlow,
  useStore,
  MarkerType,
} from "reactflow";

import { computeLayout } from "./layoutUtils";

// Add this new function at the top of the file
const calculateNodeDimensions = (nodeType, data) => {
  switch (nodeType) {
    case 'evaluation':
      // EvaluationCard has a fixed width of 400px and variable height
      // We'll estimate the height based on the content
      const baseHeight = 160; // Base height for an evaluation with 2 metrics
      const labelerCount = data.labelers?.length || 0;
      const heightPerMetric = (288 - 190 - 2*baseHeight) / (3 - 1); // Slope: (height difference) / (metric difference)
      const estimatedHeight = baseHeight + (labelerCount * heightPerMetric);
      return { width: 400, height: Math.round(estimatedHeight) };
    case 'lmp':
      // LMPNode is more compact, using a Card component
      // The size might vary based on the LMP name length
      const nameLength = data.name?.length || 0;
      const lmpWidth = Math.max(180, (80 + nameLength * 15)); // Min 180px, max 300px
      return { width: lmpWidth, height: 100 };
    default:
      // Default size for unknown node types
      return { width: 150, height: 60 };
  }
};

/**
 * Generates the initial graph structure from LMPs, traces, and evaluations.
 * @param {Array} lmps - List of LMP objects.
 * @param {Array} traces - List of trace objects.
 * @param {Array} evals - List of evaluation objects.
 * @returns {Object} - Contains initial nodes and edges.
 */
export const getInitialGraph = (lmps, traces, evals = []) => {
  if(!lmps || !traces) return { initialNodes: [], initialEdges: [] };
  const lmpIds = new Set(lmps.map(lmp => lmp.lmp_id));
  const evalLmpIds = new Set();
  const lmpToEvalMap = new Map();

  // Create evaluation nodes and map LMPs to their evaluations
  const evalNodes = (evals || []).map(eval_ => {
    eval_.labelers.forEach(labeler => {
      evalLmpIds.add(labeler.labeling_lmp_id);
      lmpToEvalMap.set(labeler.labeling_lmp_id, eval_.id);
    });
    const dimensions = calculateNodeDimensions('evaluation', eval_);
    return {
      id: `${eval_.id}`,
      type: "evaluation",
      data: { 
        label: eval_.name, 
        evaluation: eval_,
        ...dimensions
      },
      position: { x: 0, y: 0 },
    };
  });

  // Create LMP nodes, excluding those that are part of evaluations and those of type "metric"
  const lmpNodes = lmps.filter(Boolean)
    .filter(lmp => !evalLmpIds.has(lmp.lmp_id) && lmp.lmp_type !== "LABELER")
    .map(lmp => {
      const dimensions = calculateNodeDimensions('lmp', lmp);
      console.log(lmp);
      return {
        id: `${lmp.lmp_id}`,
        type: "lmp",
        data: { 
          label: lmp.name, 
          lmp,
          isEvalLabeler: evalLmpIds.has(lmp.lmp_id),
          ...dimensions
        },
        position: { x: 0, y: 0 },
      };
    });

  const deadNodes = lmps.flatMap(lmp => 
    (lmp.uses || [])
      .filter(use => !lmpIds.has(use.lmp_id) && !evalLmpIds.has(use.lmp_id))
      .map(use => {
        const dimensions = calculateNodeDimensions('lmp', use);
        return {
          id: `${use.lmp_id}`,
          type: "lmp",
          data: {
            label: `Outdated LMP ${use.name}`,
            lmp: {
              lmp_id: use.lmp_id,
              name: `Outdated LMP (${use.name})`,
              version_number: use.version_number,
            },
            ...dimensions
          },
          position: { x: 0, y: 0 },
          style: { opacity: 0.5 },
        };
      })
  );

  const initialNodes = [...evalNodes, ...lmpNodes, ...deadNodes];

  const initialEdges = lmps.flatMap(lmp => 
    lmp.is_old ? [] : (lmp.uses || []).map(use => {
      const sourceId = evalLmpIds.has(use.lmp_id) ? lmpToEvalMap.get(use.lmp_id) : `${use.lmp_id}`;
      const targetId = evalLmpIds.has(lmp.lmp_id) ? lmpToEvalMap.get(lmp.lmp_id) : `${lmp.lmp_id}`;
      return {
        id: `uses-${sourceId}-${targetId}`,
        source: sourceId,
        sourceHandle: "uses",
        target: targetId,
        targetHandle: "usedby",
        animated: false,
        type: "default",
      };
    })
  );

  traces?.forEach(trace => {
    const sourceId = evalLmpIds.has(trace.consumed) ? lmpToEvalMap.get(trace.consumed) : `${trace.consumed}`;
    const targetId = evalLmpIds.has(trace.consumer) ? lmpToEvalMap.get(trace.consumer) : `${trace.consumer}`;
    initialEdges.push({
      id: `trace-${sourceId}-${targetId}`,
      source: sourceId,
      sourceHandle: "outputs",
      target: targetId,
      targetHandle: "inputs",
      animated: true,
      markerEnd: { type: MarkerType.ArrowClosed, width: 30, height: 30 },
      style: { stroke: "#ff7f50", strokeWidth: 1 },
      labelStyle: { fill: "#ff7f50", fontWeight: 700 },
    });
  });

  computeLayout(initialNodes, initialEdges);
  return { initialNodes, initialEdges };
};
