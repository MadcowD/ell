import {
    forceSimulation,
    forceLink,
    forceManyBody,
    forceX,
    forceY,
  } from "d3-force";


import { useMemo } from "react";

import ReactFlow, {
  Panel,
  useNodesState,
  useEdgesState,
  useReactFlow,
  Background,
  Controls,
  Handle,
  useStore,
  Position,
  ReactFlowProvider,
} from "reactflow";

  
import collide from "./collide";

const simulation = forceSimulation()
  .force("charge", forceManyBody().strength(-1000))
  .force("x", forceX().x(0).strength(0.05))
  .force("y", forceY().y(0).strength(0.05))
  .force("collide", collide())
  .alphaTarget(0.05)
  .stop();

  function getLayout(nodes, edges) {
    const nodeMap = nodes.reduce((map, node) => {
      map[node.id] = node;
      return map;
    }, {});
  
    /* An algorithm that counts the number of references each node has:
      For each ndoe get all of its children and add 1
      Then we can put the y coordinate as the number of references
      as for X we'll jsut go through each level of reference #'s and add 1
    */
    // Create a map to store the number of references each node has
    const referenceCount = nodes.reduce((map, node) => {
      map[node.id] = 0;
      return map;
    }, {});
  
    function increaseReferenceCountOfFamilyTree(node, visited = null) {
      if (!visited) visited = new Set();
      if (visited.has(node.id)) return;
      visited.add(node.id);
      edges
        .filter((edge) => edge.source === node.id)
        .forEach((edge) => {
          referenceCount[edge.target] += 1;
          increaseReferenceCountOfFamilyTree(nodeMap[edge.target], visited);
        });
    }
    nodes.forEach((node) => {
      increaseReferenceCountOfFamilyTree(node);
    });
  
    // Group nodes by all the unique reference count levels
    const referenceCountLevels = new Set(Object.values(referenceCount));
    referenceCountLevels.forEach((level) => {
      // get all the nodes at this level
      const nodesAtLevel = Object.entries(referenceCount)
        .filter(([id, count]) => count === level)
        .map(([id, count]) => nodeMap[id]);
      // for each node at this level, set its x coordinate to be the index of the node
      nodesAtLevel.forEach((node, i) => {
        node.position.x = -i * 100;
        node.position.y = -level * 100;
      });
    });
  }

export const useLayoutedElements = () => {
  const { getNodes, setNodes, getEdges, fitView } = useReactFlow();
  const initialised = useStore((store) =>
    [...store.nodeInternals.values()].every((node) => node.width && node.height)
  );

  return useMemo(() => {
    let nodes = getNodes().map((node) => ({
      ...node,
      x: node.position.x,
      y: node.position.y,
    }));
    let edges = getEdges().map((edge) => edge);
    let running = false;

    // If React Flow hasn't initialised our nodes with a width and height yet, or
    // if there are no nodes in the flow, then we can't run the simulation!
    if (!initialised || nodes.length === 0) return [false, {}];

    simulation.nodes(nodes).force(
      "link",
      forceLink(edges)
        .id((d) => d.id)
        .strength(0.05)
        .distance(100)
    );



    // The tick function is called every animation frame while the simulation is
    // running and progresses the simulation one step forward each time.
    const tick = () => {
      getNodes().forEach((node, i) => {
        const dragging = Boolean(
          document.querySelector(`[data-id="${node.lmp_id}"].dragging`)
        );

        // Setting the fx/fy properties of a node tells the simulation to "fix"
        // the node at that position and ignore any forces that would normally
        // cause it to move.
        nodes[i].fx = dragging ? node.position.x : null;
        nodes[i].fy = dragging ? node.position.y : null;
      });

      simulation.tick();
      setNodes(
        nodes.map((node) => ({ ...node, position: { x: node.x, y: node.y } }))
      );

      window.requestAnimationFrame(() => {
        // Give React and React Flow a chance to update and render the new node
        // positions before we fit the viewport to the new layout.
        // fitView();

        // If the simulation hasn't be stopped, schedule another tick.
        if (running) tick();
      });
    };

    const toggle = () => {
      running = !running;
      running && window.requestAnimationFrame(tick);
    };

    const isRunning = () => running;

    return [true, { toggle, isRunning }];
  }, [initialised]);
};


export function getInitialGraph(lmps) {
  const initialNodes =
    lmps
      .filter((x) => !!x)
      .map((lmp) => {
        return {
          id: `${lmp.lmp_id}`,
          type: "lmp",
          data: { label: lmp.name, lmp },
          position: { x: 0, y: 0 },
        };
      }) || [];

  // Connect the mby their uses
  const initialEdges =
    lmps
      .filter((x) => !!x)
      .flatMap((lmp) => {
        if (lmp.is_old) return [];
        return (
          lmp?.uses?.map((use) => {
            return {
              id: `${lmp.lmp_id}-${use}`,
              target: `${lmp.lmp_id}`,
              source: `${use}`,
              animated: true,
            };
          }) || []
        );
      }) || [];
    
  getLayout(initialNodes, initialEdges);

  return { initialEdges, initialNodes };
}