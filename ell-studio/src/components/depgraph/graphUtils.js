import {
  forceSimulation,
  forceLink,
  forceManyBody,
  forceX,
  forceY,
} from "d3-force";

import { useMemo } from "react";
import ReactFlow, {
  useReactFlow,
  useStore,
  MarkerType,
} from "reactflow";

import collide from "./collide";

// Initialize the D3 force simulation
const simulation = forceSimulation()
  .force("charge", forceManyBody().strength(-1000))
  .force("x", forceX(0).strength(0.03))
  .force("y", forceY(0).strength(0.03))
  .force("collide", collide())
  .alphaTarget(0.05)
  .stop();

/**
 * Maps nodes by ID and initializes reference counts.
 * @param {Array} nodes - List of node objects.
 * @returns {Object} - Contains nodeMap and referenceCount.
 */
const initializeNodes = (nodes) => {
  const nodeMap = {};
  const referenceCount = {};
  nodes.forEach(node => {
    nodeMap[node.id] = node;
    referenceCount[node.id] = 0;
  });
  return { nodeMap, referenceCount };
};

/**
 * Recursively increments reference counts for dependencies.
 * @param {Object} node - Current node.
 * @param {Object} nodeMap - Mapping of node IDs to nodes.
 * @param {Array} edges - List of edge objects.
 * @param {Object} referenceCount - Reference counts.
 * @param {Set} visited - Visited nodes to prevent cycles.
 */
const incrementRefs = (node, nodeMap, edges, referenceCount, visited = new Set()) => {
  if (visited.has(node.id)) return;
  visited.add(node.id);
  edges
    .filter(edge => edge.source === node.id && edge.sourceHandle !== "outputs")
    .forEach(edge => {
      referenceCount[edge.target]++;
      incrementRefs(nodeMap[edge.target], nodeMap, edges, referenceCount, visited);
    });
};

/**
 * Performs a cycle-aware topological sort.
 * @param {Array} nodes - List of node objects.
 * @param {Array} edges - List of edge objects.
 * @returns {Array} - Ordered list of node IDs.
 */
const getTraceOrder = (nodes, edges) => {
  const traceOrder = [];
  const visited = new Set();
  const tempVisited = new Set();

  const dfs = (nodeId) => {
    if (tempVisited.has(nodeId) || visited.has(nodeId)) return;
    tempVisited.add(nodeId);
    edges
      .filter(edge => edge.source === nodeId && edge.sourceHandle === "outputs")
      .forEach(edge => dfs(edge.target));
    tempVisited.delete(nodeId);
    visited.add(nodeId);
    traceOrder.unshift(nodeId);
  };

  nodes.forEach(node => !visited.has(node.id) && dfs(node.id));
  return traceOrder;
};

/**
 * Assigns positions to nodes based on trace order and reference counts.
 * @param {Array} nodes - List of node objects.
 * @param {Array} edges - List of edge objects.
 */
const assignPositions = (nodes, edges) => {
  const { nodeMap, referenceCount } = initializeNodes(nodes);
  nodes.forEach(node => incrementRefs(node, nodeMap, edges, referenceCount));
  
  const traceOrder = getTraceOrder(nodes, edges);
  traceOrder.forEach((id, idx) => nodeMap[id].position.x = idx * 60);
  
  [...new Set(Object.values(referenceCount))].sort((a, b) => a - b)
    .forEach(level => {
      nodes
        .filter(node => referenceCount[node.id] === level)
        .forEach((node, i) => {
          node.position.y = -level * 100 + Math.random() * 10;
        });
    });
};

/**
 * Computes the initial layout of the graph.
 * @param {Array} nodes - List of node objects.
 * @param {Array} edges - List of edge objects.
 */
const computeLayout = (nodes, edges) => nodes.length && assignPositions(nodes, edges);

/**
 * Custom hook to manage layouted elements within React Flow.
 * @returns {Array} - Tuple containing a boolean and control methods.
 */
export const useLayoutedElements = () => {
  const { getNodes, setNodes, getEdges } = useReactFlow();
  const isInitialized = useStore(store => 
    [...store.nodeInternals.values()].every(node => node.width && node.height)
  );

  return useMemo(() => {
    if (!isInitialized || !getNodes().length) return [false, {}];

    const nodes = getNodes().map(node => ({ ...node, x: node.position.x, y: node.position.y }));
    const edges = getEdges();

    simulation.nodes(nodes).force("link", forceLink(edges).id(d => d.id).strength(0.1).distance(100));

    let isRunning = false;

    const tick = () => {
      nodes.forEach(node => {
        const dragging = Boolean(document.querySelector(`[data-id="${node.lmp_id}"].dragging`));
        node.fx = dragging ? node.position.x : null;
        node.fy = dragging ? node.position.y : null;
      });

      simulation.tick();
      setNodes(nodes.map(node => ({ ...node, position: { x: node.x, y: node.y } })));

      if (isRunning) requestAnimationFrame(tick);
    };

    const toggleSimulation = () => {
      isRunning = !isRunning;
      if (isRunning) requestAnimationFrame(tick);
    };

    return [true, { toggle: toggleSimulation, isRunning: () => isRunning }];
  }, [isInitialized, getNodes, getEdges, setNodes]);
};

/**
 * Generates the initial graph structure from LMPs and traces.
 * @param {Array} lmps - List of LMP objects.
 * @param {Array} traces - List of trace objects.
 * @returns {Object} - Contains initial nodes and edges.
 */
export const getInitialGraph = (lmps, traces) => {
  const lmpIds = new Set(lmps.map(lmp => lmp.lmp_id));

  const initialNodes = lmps.filter(Boolean).map(lmp => ({
    id: `${lmp.lmp_id}`,
    type: "lmp",
    data: { label: lmp.name, lmp },
    position: { x: 0, y: 0 },
  }));

  const deadNodes = lmps.flatMap(lmp => 
    (lmp.uses || [])
      .filter(use => !lmpIds.has(use.lmp_id))
      .map(use => ({
        id: `${use.lmp_id}`,
        type: "lmp",
        data: {
          label: `Outdated LMP ${use.name}`,
          lmp: {
            lmp_id: use.lmp_id,
            name: `Outdated LMP (${use.name})`,
            version_number: use.version_number,
          },
        },
        position: { x: 0, y: 0 },
        style: { opacity: 0.5 },
      }))
  );

  initialNodes.push(...deadNodes);

  const initialEdges = lmps.flatMap(lmp => 
    lmp.is_old ? [] : (lmp.uses || []).map(use => ({
      id: `uses-${lmp.lmp_id}-${use.lmp_id}`,
      target: `${lmp.lmp_id}`,
      source: `${use.lmp_id}`,
      animated: false,
      type: "default",
    }))
  );

  traces?.forEach(trace => {
    initialEdges.push({
      id: `trace-${trace.consumed}-${trace.consumer}`,
      source: `${trace.consumed}`,
      sourceHandle: "outputs",
      target: `${trace.consumer}`,
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