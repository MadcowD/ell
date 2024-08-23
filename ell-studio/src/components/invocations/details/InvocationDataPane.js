import React, { useState, useEffect, useMemo } from "react";
import { lstrCleanStringify } from '../../../utils/lstrCleanStringify';
import { CodeSection } from '../../source/CodeSection';

const InvocationDataPane = ({ invocation }) => {
  const [inputExpanded, setInputExpanded] = useState(true);
  const [outputExpanded, setOutputExpanded] = useState(true);

  const argsLines = useMemo(() => {
    return invocation.args.length > 0 ? lstrCleanStringify(invocation.args, 1) : null;
  }, [invocation.args]);

  const kwargsLines = useMemo(() => {
    return lstrCleanStringify(invocation.kwargs, 1);
  }, [invocation.kwargs]);

  const hasKwargs = useMemo(() => {
    return Object.keys(invocation.kwargs).length > 0;
  }, [invocation.kwargs]);

  // TODO: Properly implement collapse behaviour
  useEffect(() => {
    if ((argsLines && argsLines.split('\n').length > 10) || (hasKwargs && kwargsLines.split('\n').length > 10)) {
      setInputExpanded(false);
    }
  }, []);

  return (
    <div className="flex-grow p-4 overflow-y-auto w-[400px] hide-scrollbar">
      {argsLines && (
        <CodeSection
          title="Args"
          code={argsLines}
          showCode={inputExpanded}
          setShowCode={setInputExpanded}
          collapsedHeight={'300px'}
          lines={argsLines.split('\n').length}
          language="json"
          showLineNumbers={false}
          enableFormatToggle={true}
        />
      )} 

      {hasKwargs && (
        <CodeSection
          title="Kwargs"
          code={kwargsLines}
          showCode={inputExpanded}
          setShowCode={setInputExpanded}
          collapsedHeight={'300px'}
          lines={kwargsLines.split('\n').length}
          showLineNumbers={false}
          enableFormatToggle={true}
        />
      )}

      {invocation.results.map((result, index) => (
        <CodeSection
          key={index}
          title={`Output ${index + 1}`}
          code={result.content}
          showCode={outputExpanded}
          setShowCode={setOutputExpanded}
          lines={result.content.split('\n').length}
          language="text"
          showLineNumbers={false}
        />
      ))}
    </div>
  );
};

export default InvocationDataPane;