import React, { useMemo } from 'react';
import { Prism as SyntaxHighlighter, createElement } from 'react-syntax-highlighter';
import { atomDark as theme } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { useCallback } from 'react';

const highlightLine = (lineNumber, markLines, color = "#293645") => {
  const style = { display: "block", width: "fit-content" };
  if (markLines.includes(lineNumber)) {
    style.backgroundColor = color;
    style.color = "#90cdf4";
  }
  return { style };
};

const BoundedVariableWrapper = ({ children }) => {
  return (
    <div className="relative rounded border border-gray-500 mt-2 pt-1 px-1 pb-1">
      <span className="absolute -top-2 left-2 bg-gray-800 px-1 text-[0.6rem] text-gray-400">
        bound global at definition
      </span>
      {children}
    </div>
  );
};

export function CodeHighlighter({
  code,
  highlighterStyle = {},
  language = 'python',
  showLineNumbers = true,
  startingLineNumber = 1,
}) {
    const { cleanedCode, bvLines } = useMemo(() => {
        const bvLines = [];
        const lines = code.split('\n');
        const cleanedLines = []
        let cleanedLineIndex = 0;
        for (let index = 0; index < lines.length; index++) {
            const line = lines[index];
            if (line.includes("#<BV>")) {
                bvLines.push([cleanedLineIndex]);
            } else if (line.includes("#</BV>") && bvLines[bvLines.length - 1]?.length === 1) {
                bvLines[bvLines.length - 1].push(cleanedLineIndex - 1);
            } else {
                cleanedLines.push(line);
                cleanedLineIndex++;
            }
        }
        const cleanedCode = cleanedLines.join('\n');
        return { cleanedCode, bvLines };
    }, [code]);

    const renderer = useCallback(({ rows, stylesheet, useInlineStyles }) => {
        // list of tuples in which source lienbs are contained wihtin "#<BV>" and #</BV>
        const rowsElements =  rows.map((node, i) => {
          const transformNodes = (node) => {

            return node;
          };
          node = transformNodes(node);

    
          return createElement({
            node,
            stylesheet,
            useInlineStyles,
            key: `code-segement${i}`,
          });
        })
        // Group rows by BV (Bounded Variable) intervals
        const rowTree = [];
        let curBvSubtree = null;

        for (let i = 0; i < rowsElements.length; i++) {
            
            const containingBvInterval = bvLines.some(([start, end]) => start <= i && i <= end);
            console.log(i, containingBvInterval)
            if ((!containingBvInterval)) {
                if (curBvSubtree !== null) {
                    console.log("HI IM DOING MA", curBvSubtree)
                    rowTree.push(
                        <BoundedVariableWrapper key={`bv-${i}`}>
                            {curBvSubtree}
                        </BoundedVariableWrapper>
                    );
                    curBvSubtree = null;
                }
                rowTree.push(<div className='px-1' key={i}>{rowsElements[i]}</div>);
            } else {
                if (curBvSubtree === null) {
                    curBvSubtree = [];
                }
                curBvSubtree.push(rowsElements[i]);
            }
        }
        if(curBvSubtree !== null) {
            rowTree.push(
                <BoundedVariableWrapper key={`bv-end`}>
                    {curBvSubtree}
                </BoundedVariableWrapper>
            );
        }

        return rowTree;

      }, [bvLines]);

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
