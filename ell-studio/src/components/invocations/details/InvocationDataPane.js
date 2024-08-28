import React, { useState, useEffect, useMemo } from "react";
import { lstrCleanStringify } from '../../../utils/lstrCleanStringify';
import { CodeSection } from '../../source/CodeSection';
import IORenderer from '../../IORenderer';

const InvocationDataPane = ({ invocation }) => {
  const [inputExpanded, setInputExpanded] = useState(true);
  const [outputExpanded, setOutputExpanded] = useState(true);


  const kwargsLines = useMemo(() => {
    return lstrCleanStringify(invocation.contents?.params, 1);
  }, [invocation.contents?.params]);

  const resultsLines = useMemo(() => {
    return lstrCleanStringify(invocation.contents?.results, 1);
  }, [invocation.contents?.results]);

  const hasKwargs = useMemo(() => {
    return Object.keys(invocation.contents?.params).length > 0;
  }, [invocation.contents?.params]);

  const hasResults = useMemo(() => {
    return Array.isArray(invocation.contents?.results) ? invocation.contents?.results.length > 0 : !!invocation.contents?.results;
  }, [invocation.contents?.results]);

  // TODO: Properly implement collapse behaviour
  useEffect(() => {
    if ((kwargsLines && kwargsLines.split('\n').length > 10) || (hasKwargs && kwargsLines.split('\n').length > 10)) {
      setInputExpanded(false);
    }
    if (hasResults && resultsLines.split('\n').length > 10) {
      setOutputExpanded(false);
    }
  }, [kwargsLines, resultsLines, hasKwargs, hasResults]);

  return (
    <div className="flex-grow p-4 overflow-y-auto w-[fullpx] hide-scrollbar">
      {hasKwargs && (
        <CodeSection
          title="Input"
          raw={JSON.stringify(invocation.contents?.params, null, 2)}
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
            <IORenderer content={lstrCleanStringify(invocation.contents?.params, 1)} typeMatchLevel={1} inline={false} />
          </div>
        </CodeSection>
      )}

      {hasResults && (
        <CodeSection
          title="Results"
          raw={JSON.stringify(invocation.contents?.results, null, 2)}
          showCode={outputExpanded}
          setShowCode={setOutputExpanded}
          collapsedHeight={'300px'}
          enableFormatToggle={false}
          showCopyButton={true}
          offset={0}
        > 
          <div className="p-4">
            <IORenderer content={lstrCleanStringify(invocation.contents?.results, 1)} inline={false} />
          </div>
        </CodeSection>
      )}
    </div>
  );
};

export default InvocationDataPane;