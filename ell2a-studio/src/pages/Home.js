import { Card, CardContent, CardHeader } from 'components/common/Card'
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from 'components/common/Resizable'
import { ScrollArea } from 'components/common/ScrollArea'
import React, { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { DependencyGraph } from '../components/depgraph/DependencyGraph'
import VersionBadge from '../components/VersionBadge'
import { useTheme } from '../contexts/ThemeContext'
import { useLatestLMPs, useTraces } from '../hooks/useBackend'
import { getTimeAgo } from '../utils/lmpUtils'

const MemoizedDependencyGraph = React.memo(DependencyGraph)

function Home() {
    const [expandedLMP, setExpandedLMP] = useState(null)
    const { darkMode } = useTheme()
    const { data: lmps, isLoading: isLoadingLMPs } = useLatestLMPs()
    const { data: traces, isLoading: isLoadingTraces } = useTraces(lmps)

    const toggleExpand = (lmpName, event) => {
        if (event.target.tagName.toLowerCase() !== 'a') {
            setExpandedLMP(expandedLMP === lmpName ? null : lmpName)
        }
    }

    const truncateId = (id) => {
        return id.length > 8 ? `${id.substring(0, 8)}...` : id
    }

    const [firstTraces, setFirstTraces] = useState(traces)
    const [firstLMPs, setFirstLMPs] = useState(lmps)

    useEffect(() => {
        if ((!firstTraces || !firstLMPs) && traces && lmps) {
            console.log('Setting first traces and lmps')
            setFirstTraces(traces)
            setFirstLMPs(lmps)
        }
    }, [traces, firstTraces, lmps, firstLMPs])

    // TODO: Make graph dynamically update.
    const memoizedTraces = useMemo(() => firstTraces, [firstTraces])
    const memoizedLMPs = useMemo(() => firstLMPs, [firstLMPs])

    if (isLoadingLMPs || isLoadingTraces) {
        return (
            <div className={`bg-background min-h-screen flex items-center justify-center`}>
                <p className={`text-foreground`}>Loading...</p>
            </div>
        )
    }

    if (!memoizedLMPs || memoizedLMPs.length === 0) {
        return (
            <div className={`bg-background min-h-screen flex items-center justify-center`}>
                <Card className="w-3/4 max-w-2xl">
                    <CardHeader>
                        <h2 className="text-2xl font-semibold text-foreground">No LMPs Found</h2>
                    </CardHeader>
                    <CardContent>
                        <p className="text-muted-foreground mb-4">
                            It looks like you don't have any Language Model Programs (LMPs) in your storage directory
                            yet.
                        </p>
                        <p className="text-muted-foreground mb-4">
                            To get started with versioning your LMPs, try the following example:
                        </p>
                        <pre className="bg-muted p-4 rounded-md overflow-x-auto">
                            <code className="text-sm">
                                {`import ell2a

ell2a.init(store='./logdir', autocommit=True)

@ell2a.simple(model="gpt-4o")
def hello(name: str):
    """You are a helpful assistant."""
    return f"Say hello to {name}!"

greeting = hello("Sam Altman")
print(greeting)`}
                            </code>
                        </pre>
                        <p className="text-muted-foreground mt-4">
                            Run this script, then refresh this page to see your first versioned LMP.
                        </p>
                    </CardContent>
                </Card>
            </div>
        )
    }

    return (
        <div className={`bg-background min-h-screen`}>
            <ResizablePanelGroup direction="horizontal" className="w-full h-screen">
                <ResizablePanel defaultSize={70} minSize={30}>
                    <div className="flex flex-col h-full">
                        <div className="flex items-center justify-between border-b border-border p-4">
                            <span className="text-xl font-medium text-foreground flex items-center">
                                Language Model Programs
                            </span>
                            <div className="flex items-center">
                                <span className="mr-4 text-sm text-muted-foreground">Total LMPs: {lmps.length}</span>
                                <span className="text-sm text-muted-foreground">
                                    Last Updated:{' '}
                                    {lmps[0] && lmps[0].versions && lmps[0].versions[0]
                                        ? getTimeAgo(lmps[0].versions[0].created_at)
                                        : 'N/A'}
                                </span>
                            </div>
                        </div>
                        <div className="w-full h-full">
                            <MemoizedDependencyGraph
                                lmps={memoizedLMPs}
                                traces={memoizedTraces}
                                key={memoizedLMPs.length + memoizedTraces.length}
                            />
                        </div>
                    </div>
                </ResizablePanel>
                <ResizableHandle withHandle />
                <ResizablePanel defaultSize={30} minSize={20}>
                    <ScrollArea className="h-screen">
                        <div className="space-y-4 p-4">
                            {lmps.map((lmp) => (
                                <Link
                                    to={`/lmp/${lmp.name}`}
                                    className="flex cursor-pointer hover:bg-accent/50 transition-colors duration-200"
                                    onClick={(e) => e.stopPropagation()}>
                                    <Card
                                        key={lmp.name}
                                        className="cursor-pointer hover:bg-accent/50 rounded transition-colors duration-200"
                                        onClick={(e) => toggleExpand(lmp.name, e)}>
                                        <CardHeader>
                                            <div className="flex flex-col space-y-2">
                                                <div className="text-xl font-semibold text-foreground hover:text-primary break-words cursor-pointer">
                                                    {lmp.name}
                                                </div>
                                                <div className="flex space-x-2">
                                                    <span className="text-xs px-2 py-1 rounded-full bg-muted text-muted-foreground">
                                                        ID: {truncateId(lmp.lmp_id)}
                                                    </span>
                                                    <span className="text-xs px-2 py-1 rounded-full bg-primary text-primary-foreground">
                                                        Latest
                                                    </span>
                                                    <VersionBadge version={lmp.version_number + 1} hash={lmp.lmp_id} />
                                                </div>
                                            </div>
                                        </CardHeader>
                                        <CardContent>
                                            <div className="bg-muted rounded p-3 mb-4">
                                                <code className="text-sm text-muted-foreground">
                                                    {lmp.source.length > 100
                                                        ? `${lmp.source.substring(0, 100)}...`
                                                        : lmp.source}
                                                </code>
                                            </div>
                                        </CardContent>
                                    </Card>
                                </Link>
                            ))}
                        </div>
                    </ScrollArea>
                </ResizablePanel>
            </ResizablePanelGroup>
        </div>
    )
}

export default Home
