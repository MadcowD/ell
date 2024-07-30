import React, { useMemo, useCallback } from 'react';
import { Prism as SyntaxHighlighter, createElement } from 'react-syntax-highlighter';
import { atomDark as theme } from 'react-syntax-highlighter/dist/esm/styles/prism';

const highlightLine = (lineNumber, markLines, color = "#293645") => {
  const style = { display: "block", width: "fit-content" };
  if (markLines.includes(lineNumber)) {
    style.backgroundColor = color;
    style.color = "#90cdf4";
  }
  return { style };
};

export function CodeHighlighter({
  code,
  highlighterStyle = {},
  language = 'python',
  showLineNumbers = true,
  startingLineNumber = 1,
  customHooks = [], // New prop for custom hooks
  defaultRowPadding = 'px-1', // New parameter for default row padding
}) {
  const { cleanedCode, hookRanges } = useMemo(() => {
    const hookRanges = customHooks.map(() => []);
    const lines = code.split('\n');
    const cleanedLines = [];
    let cleanedLineIndex = 0;

    for (let index = 0; index < lines.length; index++) {
      const line = lines[index];
      let skipLine = false;

      // eslint-disable-next-line no-loop-func
      customHooks.forEach((hook, hookIndex) => {
        if (line.includes(hook.startTag)) {
          hookRanges[hookIndex].push([cleanedLineIndex]);
          skipLine = true;
        } else if (line.includes(hook.endTag) && hookRanges[hookIndex][hookRanges[hookIndex].length - 1]?.length === 1) {
          hookRanges[hookIndex][hookRanges[hookIndex].length - 1].push(cleanedLineIndex - 1);
          // also push all of the clean code in the hook range
          const contentHook = cleanedLines.slice(hookRanges[hookIndex][hookRanges[hookIndex].length - 1][0], cleanedLineIndex).join('\n');
          hookRanges[hookIndex][hookRanges[hookIndex].length - 1].push(contentHook);
          skipLine = true;
        }
      });

      if (!skipLine) {
        cleanedLines.push(line);
        cleanedLineIndex++;
      }
    }

    const cleanedCode = cleanedLines.join('\n');
    return { cleanedCode, hookRanges };
  }, [code, customHooks]);

  const renderer = useCallback(({ rows, stylesheet, useInlineStyles }) => {
    const rowsElements = rows.map((node, i) => 
      createElement({
        node,
        stylesheet,
        useInlineStyles,
        key: `code-segment${i}`,
      })
    );

    const rowTree = [];
    const activeHooks = customHooks.map(() => null);

    for (var i = 0; i < rowsElements.length; i++) {
      let currentElement = <div className={defaultRowPadding} key={i}>{rowsElements[i]}</div>;

      // eslint-disable-next-line no-loop-func
      customHooks.forEach((hook, hookIndex) => {
        const containingInterval = hookRanges[hookIndex].some(([start, end, _]) => start <= i && i <= end);

        if (containingInterval) {
          if (activeHooks[hookIndex] === null) {
            activeHooks[hookIndex] = [];
          }
          activeHooks[hookIndex].push(currentElement);
          currentElement = null;
        } else if (activeHooks[hookIndex] !== null) {
          currentElement = hook.wrapper({
            children: activeHooks[hookIndex],
            content: hookRanges[hookIndex].find(([start, end, contents]) => start <= i && i <= end)[2],
            key: `${hook.name}-${i}`,
          });
          activeHooks[hookIndex] = null;
        }
      });

      if (currentElement) {
        rowTree.push(currentElement);
      }
    }

    customHooks.forEach((hook, hookIndex) => {
      if (activeHooks[hookIndex] !== null) {
         rowTree.push(hook.wrapper({
          children: activeHooks[hookIndex],
          key: `${hook.name}-end`,
          content: hookRanges[hookIndex].find(([start, end, contents]) => start <= i )[2],
        }));
      }
    });

    return rowTree;
  }, [hookRanges, customHooks, defaultRowPadding]); // Add defaultRowPadding to dependencies

  return (
    <SyntaxHighlighter
      language={language}
      style={theme}
      showLineNumbers={showLineNumbers}
      startingLineNumber={startingLineNumber}
      customStyle={{
        margin: 0,
        padding: '1em',
        borderRadius: '0 0 6px 6px',
        ...highlighterStyle,
      }}
      wrapLines
      renderer={renderer}
    >
      {cleanedCode}
    </SyntaxHighlighter>
  );
}