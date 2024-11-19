import React, { useState, useMemo } from "react";
import { CodeSection } from '../../source/CodeSection';
import IORenderer from '../../IORenderer';
import MetricDisplay from '../../evaluations/MetricDisplay';
import { FiBarChart2 } from 'react-icons/fi';
const SkeletonLoader = () => (
  <div className="animate-pulse space-y-2">
    <div className="h-4 bg-gray-200 rounded w-3/4"></div>
    <div className="h-4 bg-gray-200 rounded"></div>
    <div className="h-4 bg-gray-200 rounded w-5/6"></div>
    <div className="h-4 bg-gray-200 rounded w-2/3"></div>
  </div>
);

const InvocationDataPane = ({ invocation }) => {
  const [inputExpanded, setInputExpanded] = useState(true);
  const [outputExpanded, setOutputExpanded] = useState(true);

  const isExternalLoading = invocation.contents?.is_external && !invocation.contents?.is_external_loaded;

  const hasKwargs = useMemo(() => {
    return typeof invocation.contents?.params === 'object' && 
           invocation.contents?.params !== null && 
           Object.keys(invocation.contents.params).length > 0;
  }, [invocation.contents?.params]);

  const hasResults = useMemo(() => {
    return Array.isArray(invocation.contents?.results) ? 
           invocation.contents.results.length > 0 : 
           invocation.contents?.results !== null && 
           invocation.contents?.results !== undefined;
  }, [invocation.contents?.results]);

  const metrics = useMemo(() => {
    console.log('InvocationDataPane metrics calculation:', {
      hasLabels: !!invocation.labels,
      labels: invocation.labels
    });

    if (!invocation.labels?.length) return null;
    return invocation.labels.map(label => ({
      labelerId: label.labeler_id,
      value: label.label_invocation?.contents?.results,
      name: label.labeler_name || label.labeler_id.split('-')[3] || 'Score'
    }));
  }, [invocation.labels]);

  const renderCodeSection = (title, content, expanded, setExpanded, typeMatchLevel) => (
    <CodeSection
      title={title}
      raw={isExternalLoading ? "Loading..." : JSON.stringify(content, null, 2)}
      showCode={expanded}
      setShowCode={setExpanded}
      collapsedHeight={'300px'}
      lines={1}
      showLineNumbers={false}
      offset={0}
      enableFormatToggle={false}
      showCopyButton={!isExternalLoading}
    >
      <div className="p-4">
        {isExternalLoading ? (
          <SkeletonLoader />
        ) : (
          <IORenderer content={content} typeMatchLevel={typeMatchLevel} inline={false} />
        )}
      </div>
    </CodeSection>
  );

  return (
    <div className="flex-grow p-4 overflow-y-auto w-[fullpx] hide-scrollbar">
      {/* Metrics Section */}
      {metrics && metrics.length > 0 && (
        <div className="mb-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {metrics.map((metric, index) => (
              <>
                <div 
                  key={metric.labelerId}
                  className="flex flex-row items-center justify-between text-xs py-1 hover:bg-accent/50 transition-colors duration-100 pr-1"
                >
                  <div className="font-medium truncate flex items-center" title={metric.name}>
                    <FiBarChart2 className="mr-1 h-3 w-3 text-muted-foreground flex-shrink-0" />
                    <code className="metric-label text-xs font-medium  max-w-[calc(100%-1.5rem)]">
                      {metric.name}
                    </code>
                  </div>
                  <MetricDisplay
                    currentValue={metric.value}
                    label={metric.name}
                    showTooltip={false}
                    showTrend={false}
                  />
                </div>
                {index < metrics.length - 1 && (
                  <div className="border-b border-gray-900 my-0 md:hidden" />
                )}
              </>
            ))}
          </div>
        </div>
      )}

      {(hasKwargs || isExternalLoading) && renderCodeSection(
        "Input",
        invocation.contents?.params,
        inputExpanded,
        setInputExpanded,
        1
      )}

      {(hasResults || isExternalLoading) && renderCodeSection(
        "Results",
        invocation.contents?.results,
        outputExpanded,
        setOutputExpanded,
        0
      )}
    </div>
  );
};

export default InvocationDataPane;