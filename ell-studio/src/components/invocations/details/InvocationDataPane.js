import React, { useState, useEffect, useMemo } from "react";
import { lstrCleanStringify } from '../../../utils/lstrCleanStringify';
import { CodeSection } from '../../source/CodeSection';
import IORenderer from '../../IORenderer';

const InvocationDataPane = ({ invocation }) => {
  const [inputExpanded, setInputExpanded] = useState(true);
  const [outputExpanded, setOutputExpanded] = useState(true);

  const argsLines = useMemo(() => {
    return invocation.args.length > 0 ? lstrCleanStringify(invocation.args, 1) : null;
  }, [invocation.args]);

  const kwargsLines = useMemo(() => {
    return lstrCleanStringify(invocation.kwargs, 1);
  }, [invocation.kwargs]);

  const resultsLines = useMemo(() => {
    return lstrCleanStringify(invocation.results, 1);
  }, [invocation.results]);

  const hasKwargs = useMemo(() => {
    return Object.keys(invocation.kwargs).length > 0;
  }, [invocation.kwargs]);

  const hasResults = useMemo(() => {
    return Array.isArray(invocation.results) ? invocation.results.length > 0 : !!invocation.results;
  }, [invocation.results]);

  // TODO: Properly implement collapse behaviour
  useEffect(() => {
    if ((argsLines && argsLines.split('\n').length > 10) || (hasKwargs && kwargsLines.split('\n').length > 10)) {
      setInputExpanded(false);
    }
    if (hasResults && resultsLines.split('\n').length > 10) {
      setOutputExpanded(false);
    }
  }, [argsLines, kwargsLines, resultsLines, hasKwargs, hasResults]);

  return (
    <div className="flex-grow p-4 overflow-y-auto w-[fullpx] hide-scrollbar">
      {hasKwargs && (
        <CodeSection
          title="Input"
          raw={JSON.stringify(invocation.kwargs, null, 2)}
          showCode={inputExpanded}
          setShowCode={setInputExpanded}
          collapsedHeight={'300px'}
          lines={kwargsLines.split('\n').length}
          showLineNumbers={false}
          offset={0}
          enableFormatToggle={false}
          showCopyButton={true}
        >
          <div className="p-4">
            <IORenderer content={lstrCleanStringify(invocation.kwargs, 1)} inline={false} />
          </div>
        </CodeSection>
      )}

      {hasResults && (
        <CodeSection
          title="Results"
          raw={JSON.stringify(invocation.results, null, 2)}
          showCode={outputExpanded}
          setShowCode={setOutputExpanded}
          collapsedHeight={'300px'}
          enableFormatToggle={false}
          showCopyButton={true}
          offset={0}
        > 
          <div className="p-4">
            <IORenderer content={lstrCleanStringify(invocation.results, 1)} inline={false} />
          </div>
        </CodeSection>
      )}
    </div>
  );
};

export default InvocationDataPane;