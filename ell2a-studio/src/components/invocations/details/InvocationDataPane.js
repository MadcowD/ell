import React, { useState, useMemo } from "react";
import { CodeSection } from '../../source/CodeSection';
import IORenderer from '../../IORenderer';

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