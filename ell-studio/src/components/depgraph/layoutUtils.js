import {
    forceSimulation,
    forceLink,
    forceManyBody,
    forceX,
    forceY,
    forceCollide,
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
    .force("charge", forceManyBody().strength(-500))
    .force("link", forceLink().id(d => d.id).distance(150))
    .force("x", forceX().strength(0.1))
    .force("y", forceY().strength(0.1))
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
 * Finds connected components in the graph.
 * @param {Array} nodes - List of node objects.
 * @param {Array} edges - List of edge objects.
 * @returns {Array} - Array of connected components, each component is an array of node IDs.
 */
const getConnectedComponents = (nodes, edges) => {
    const visited = new Set();
    const components = [];

    const dfs = (nodeId, component) => {
        visited.add(nodeId);
        component.push(nodeId);
        edges.forEach(edge => {
            if (edge.source === nodeId && !visited.has(edge.target)) {
                dfs(edge.target, component);
            } else if (edge.target === nodeId && !visited.has(edge.source)) {
                dfs(edge.source, component);
            }
        });
    };

    nodes.forEach(node => {
        if (!visited.has(node.id)) {
            const component = [];
            dfs(node.id, component);
            components.push(component);
        }
    });

    return components;
};

/**
 * Assigns positions to nodes by topologically separating groups (components),
 * laying out within the separate topological groups, and then packing them
 * in a non-overlapping way based on their bounding boxes considering node sizes.
 * @param {Array} nodes - List of node objects.
 * @param {Array} edges - List of edge objects.
 */
const assignPositions = (nodes, edges) => {
    // Get connected components
    const components = getConnectedComponents(nodes, edges);
    const allNodeMap = {};
    nodes.forEach(node => allNodeMap[node.id] = node);

    let offsetX = 0;
    let offsetY = 0;
    const groupSpacing = 100; // Base space between groups

    components.forEach((componentNodeIds, index) => {
        const componentNodes = componentNodeIds.map(id => ({ ...allNodeMap[id] }));
        const componentEdges = edges.filter(edge => componentNodeIds.includes(edge.source) && componentNodeIds.includes(edge.target));

        // Assign positions within the component
        assignPositionsToComponent(componentNodes, componentEdges);

        // Compute bounding box of the component considering node sizes
        const xs = componentNodes.map(node => node.position.x + (node.data.width || 100));
        const ys = componentNodes.map(node => node.position.y + (node.data.height || 50));
        const minX = Math.min(...componentNodes.map(node => node.position.x));
        const minY = Math.min(...componentNodes.map(node => node.position.y));
        const maxX = Math.max(...xs);
        const maxY = Math.max(...ys);
        const width = maxX - minX;
        const height = maxY - minY;

        // Offset component positions to prevent overlap
        const offsetXForGroup = offsetX - minX;
        const offsetYForGroup = offsetY - minY;

        componentNodes.forEach(node => {
            node.position.x += offsetXForGroup;
            node.position.y += offsetYForGroup;
            // Update the position in the original nodes array
            allNodeMap[node.id].position = node.position;
        });

        // Update offsetX for the next group based on current group's width
        offsetX += width + groupSpacing;

        // Optionally, arrange groups in rows if offsetX exceeds a certain limit
        // For example, start a new row after 2000px
        const maxRowWidth = 1000;
        if (offsetX > maxRowWidth) {
            offsetX = 0;
            offsetY += height + groupSpacing;
        }
    });
};

/**
 * Assigns positions to nodes within a single component based on dependencies and edge types,
 * accounting for each node's width and height to prevent overlaps.
 * @param {Array} nodes - List of node objects in the component.
 * @param {Array} edges - List of edge objects in the component.
 */
const assignPositionsToComponent = (nodes, edges) => {
    const { nodeMap, referenceCount } = initializeNodes(nodes);
    nodes.forEach(node => incrementRefs(node, nodeMap, edges, referenceCount));

    const traceOrder = getTraceOrder(nodes, edges);

    // Assign horizontal levels based on inputs/outputs
    const horizontalLevels = {};
    traceOrder.forEach(id => {
        const incomingOutputEdges = edges.filter(edge => edge.target === id && edge.sourceHandle === "outputs");
        if (incomingOutputEdges.length === 0) {
            horizontalLevels[id] = 0;
        } else {
            horizontalLevels[id] = Math.max(...incomingOutputEdges.map(edge => horizontalLevels[edge.source] + 1));
        }
    });

    // Assign vertical levels based on uses/usedby
    const verticalLevels = {};
    traceOrder.forEach(id => {
        const incomingUseEdges = edges.filter(edge => edge.target === id && edge.sourceHandle === "uses");
        if (incomingUseEdges.length === 0) {
            verticalLevels[id] = 0;
        } else {
            verticalLevels[id] = Math.max(...incomingUseEdges.map(edge => verticalLevels[edge.source] + 1));
        }
    });

    // Group nodes by horizontal and vertical levels
    const nodesByPosition = {};
    nodes.forEach(node => {
        const xLevel = horizontalLevels[node.id] || 0;
        const yLevel = verticalLevels[node.id] || 0;
        const key = `${xLevel}-${yLevel}`;
        if (!nodesByPosition[key]) nodesByPosition[key] = [];
        nodesByPosition[key].push(node);
    });

    // Determine maximum width and height per horizontal and vertical level
    const maxWidthPerXLevel = {};
    const maxHeightPerYLevel = {};

    nodes.forEach(node => {
        const xLevel = horizontalLevels[node.id] || 0;
        const yLevel = verticalLevels[node.id] || 0;
        const nodeWidth = node.data.width || 100;
        const nodeHeight = node.data.height || 50;

        if (!maxWidthPerXLevel[xLevel] || nodeWidth > maxWidthPerXLevel[xLevel]) {
            maxWidthPerXLevel[xLevel] = nodeWidth;
        }

        if (!maxHeightPerYLevel[yLevel] || nodeHeight > maxHeightPerYLevel[yLevel]) {
            maxHeightPerYLevel[yLevel] = nodeHeight;
        }
    });

    // Assign positions within the component
    let currentYOffsets = {};
    const levelSpacingX = 50; // Horizontal spacing between levels
    const levelSpacingY = 50; // Vertical spacing between levels

    Object.keys(nodesByPosition).forEach(key => {
        const [xLevel, yLevel] = key.split('-').map(Number);
        const nodesAtPosition = nodesByPosition[key];
        const maxHeight = maxHeightPerYLevel[yLevel] || 50;

        // Initialize Y offset for the xLevel if not present
        if (!currentYOffsets[xLevel]) currentYOffsets[xLevel] = 0;

        nodesAtPosition.forEach((node, index) => {
            const nodeWidth = node.data.width || 100;
            const nodeHeight = node.data.height || 50;

            node.position = {
                x: xLevel * (maxWidthPerXLevel[xLevel] + levelSpacingX),
                y: currentYOffsets[xLevel],
            };

            // Update the Y offset for the next node in this level
            currentYOffsets[xLevel] += nodeHeight + levelSpacingY;
        });
    });
};

/**
 * Computes the initial layout of the graph.
 * @param {Array} nodes - List of node objects.
 * @param {Array} edges - List of edge objects.
 */
export const computeLayout = (nodes, edges) => nodes.length && assignPositions(nodes, edges);

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
                const dragging = Boolean(document.querySelector(`[data-id="${node.id}"].dragging`));
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