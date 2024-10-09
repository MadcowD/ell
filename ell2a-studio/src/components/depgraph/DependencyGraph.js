import { Button } from 'components/common/Button'
import { Lock, Maximize, Unlock, ZoomIn, ZoomOut } from 'lucide-react'
import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import ReactFlow, {
    Background,
    Handle,
    Panel,
    Position,
    ReactFlowProvider,
    useEdgesState,
    useNodesState,
    useReactFlow
} from 'reactflow'
import 'reactflow/dist/style.css'
import { Card } from '../Card'
import { LMPCardTitle } from './LMPCardTitle' // Add this import

import { getInitialGraph, useLayoutedElements } from './graphUtils'

function LMPNode({ data }) {
    const { lmp } = data
    const onChange = useCallback((evt) => {}, [])

    return (
        <>
            <Handle type="source" position={Position.Top} />
            <Card key={lmp.lmp_id}>
                <Link to={`/lmp/${lmp.name}`}>
                    <LMPCardTitle displayVersion lmp={lmp} fontSize="sm" />
                </Link>
            </Card>
            <Handle type="target" position={Position.Bottom} id="a" />
            <Handle type="target" position={Position.Left} id="inputs" />
            <Handle type="source" position={Position.Right} id="outputs" />
        </>
    )
}

const LayoutFlow = ({ initialNodes, initialEdges }) => {
    const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
    const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)
    const [initialised, { toggle, isRunning }] = useLayoutedElements()
    const [didInitialSimulation, setDidInitialSimulation] = useState(false)
    const { fitView } = useReactFlow()

    // Start the simulation automatically when initialized and run it for 1 second
    useEffect(() => {
        if (initialised && !didInitialSimulation) {
            setDidInitialSimulation(true)
            toggle()

            fitView({ duration: 500, padding: 0.1 })
            setTimeout(() => {
                toggle()
                // Fit view after the simulation has run
                fitView({ duration: 500, padding: 0.1 })
            }, 1000)
        }
    }, [initialised, didInitialSimulation, toggle, fitView])

    const nodeTypes = useMemo(() => ({ lmp: LMPNode }), [])

    return (
        <div className="h-full relative">
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                nodeTypes={nodeTypes}>
                <Panel></Panel>
                <Background />
                <CustomControls />
            </ReactFlow>
        </div>
    )
}

function CustomControls() {
    const { zoomIn, zoomOut, fitView, setNodes } = useReactFlow()
    const [nodesLocked, setNodesLocked] = useState(false)

    const handleZoomIn = () => zoomIn({ duration: 300, step: 0.5 })
    const handleZoomOut = () => zoomOut({ duration: 300, step: 0.5 })
    const handleFitView = () => fitView({ duration: 500, padding: 0.1 })
    const handleToggleNodeLock = () => {
        setNodes((nodes) => nodes.map((node) => ({ ...node, draggable: nodesLocked })))
        setNodesLocked(!nodesLocked)
    }

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
    )
}

export function DependencyGraph({ lmps, traces, ...rest }) {
    // construct ndoes from LMPS
    const { initialEdges, initialNodes } = useMemo(() => getInitialGraph(lmps, traces), [lmps, traces])

    return (
        <div className="h-full h-full w-full border-gray-700" {...rest}>
            <ReactFlowProvider>
                <LayoutFlow initialEdges={initialEdges} initialNodes={initialNodes} />
            </ReactFlowProvider>
        </div>
    )
}
