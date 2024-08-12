import React, { useState, useMemo, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { getTimeAgo } from '../utils/lmpUtils';
import { DependencyGraph } from '../components/depgraph/DependencyGraph';
import { useLatestLMPs, useTraces } from '../hooks/useBackend';
import VersionBadge from '../components/VersionBadge';
import { BiCube } from 'react-icons/bi';
import { Card, CardHeader, CardContent } from 'components/common/Card';
import { ScrollArea } from 'components/common/ScrollArea';
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from 'components/common/Resizable';

const MemoizedDependencyGraph = React.memo(DependencyGraph);

function Home() {
  const [expandedLMP, setExpandedLMP] = useState(null);
  const { darkMode } = useTheme();
  const { data: lmps, isLoading: isLoadingLMPs } = useLatestLMPs();
  const { data: traces, isLoading: isLoadingTraces } = useTraces(lmps);

  const toggleExpand = (lmpName, event) => {
    if (event.target.tagName.toLowerCase() !== 'a') {
      setExpandedLMP(expandedLMP === lmpName ? null : lmpName);
    }
  };

  const truncateId = (id) => {
    return id.length > 8 ? `${id.substring(0, 8)}...` : id;
  };

  const [firstTraces, setFirstTraces] = useState(traces);
  const [firstLMPs, setFirstLMPs] = useState(lmps);

  useEffect(() => {
    if((!firstTraces || !firstLMPs) && traces && lmps) {
      console.log("Setting first traces and lmps");
      setFirstTraces(traces);
      setFirstLMPs(lmps);
    }
  }, [traces, firstTraces, lmps, firstLMPs]);
  
  // TODO: Make graph dynamically update.
  const memoizedTraces = useMemo(() => firstTraces, [firstTraces]);
  const memoizedLMPs = useMemo(() => firstLMPs, [firstLMPs]);

  if (!memoizedLMPs || !memoizedTraces) {
    return <div className={`bg-background min-h-screen flex items-center justify-center`}>
      <p className={`text-foreground`}>Loading...</p>
    </div>;
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
                <span className="mr-4 text-sm text-muted-foreground">
                  Total LMPs: {lmps.length}
                </span>
                <span className="text-sm text-muted-foreground">
                  Last Updated: {lmps[0] && lmps[0].versions && lmps[0].versions[0] ? getTimeAgo(lmps[0].versions[0].created_at) : 'N/A'}
                </span>
              </div>
            </div>
            <div className="w-full h-full">
              <MemoizedDependencyGraph lmps={memoizedLMPs} traces={memoizedTraces} key={memoizedLMPs.length + memoizedTraces.length}/>
            </div>
          </div>
        </ResizablePanel>
        <ResizableHandle withHandle />
        <ResizablePanel defaultSize={30} minSize={20}>
          <ScrollArea className="h-screen">
            <div className="space-y-4 p-4">
              {lmps.map((lmp) => (
                <Card 
                  key={lmp.name} 
                  className="cursor-pointer hover:bg-accent/50 transition-colors duration-200"
                  onClick={(e) => toggleExpand(lmp.name, e)}
                >
                  <CardHeader>
                    <div className="flex flex-col space-y-2">
                      <Link 
                        to={`/lmp/${lmp.name}`} 
                        className="text-xl font-semibold text-foreground hover:text-primary break-words"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {lmp.name}
                      </Link>
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
                        {lmp.source.length > 100 ? `${lmp.source.substring(0, 100)}...` : lmp.source}
                      </code>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </ScrollArea>
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
}

export default Home;