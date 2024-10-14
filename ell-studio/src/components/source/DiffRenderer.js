import React from 'react';
import { diffLines } from 'unidiff';
import { Prism as SyntaxHighlighter, createElement } from "react-syntax-highlighter";

export function DiffRenderer({
  previousCode,
  code,
  stylesheet,
  useInlineStyles,
  startingLineNumber,
  commonProps
}) {
  if (!previousCode) return null;

  function removeEllTags(code) {
    const ellTagRegex = /\s*#\s*<\/?(BV|BmV|LMP)>/g;
    return code.replace(ellTagRegex, '');
  }

  code = removeEllTags(code);
  previousCode = removeEllTags(previousCode);

  var previousCodeRows = []
  var currentCodeRows = []
  const getHighlightedCode = (code, rowsCb) => {
    SyntaxHighlighter({code, language: "python", showLineNumbers: false, renderer: ({rows}) => {
      rowsCb(rows)
    }})
  }
  getHighlightedCode(previousCode, (rows) => {
    previousCodeRows = rows
  })
  getHighlightedCode(code, (rows) => {
    currentCodeRows = rows
  })

  const diff = diffLines(previousCode, code);


  let oldLineNumber = startingLineNumber;
  let newLineNumber = startingLineNumber;
  const diffRows = [];

  let oldRowIndex = 0;
  let newRowIndex = 0;

  diff.forEach((part, partIndex) => {
    const { added, removed, value } = part;
    const lines = value.split('\n')
    if(lines.length > 1 && lines[lines.length - 1] === '') {
      lines.pop()
    }

    
    lines.forEach((line, lineIndex) => {
      const diffIndicator = added ? '+' : (removed ? '-' : ' ');
      const backgroundColor = added ? 'rgba(0, 255, 0, 0.1)' : (removed ? 'rgba(255, 0, 0, 0.1)' : 'transparent');
      
      let lineContent;
      if (removed) {
        lineContent = previousCodeRows[oldRowIndex++];

      } else if (added) {
        lineContent = currentCodeRows[newRowIndex++];
      } else {
        lineContent = currentCodeRows[newRowIndex++];
        oldRowIndex++;
      }
       // Debug: Check if we're out of bounds on currentCodeRow



       lineContent = createElement({
        node: lineContent,
        stylesheet,
        useInlineStyles,
      })

      diffRows.push(
        <div key={`${partIndex}-${lineIndex}`} style={{ display: 'flex', backgroundColor }}>
          <span style={{ width: '30px', textAlign: 'right', marginRight: '10px', userSelect: 'none', color: '#6e7681' }}>
            {!removed ? oldLineNumber : ''}
          </span>
          <span style={{ width: '30px', textAlign: 'right', marginRight: '15px', userSelect: 'none', color: '#6e7681' }}>
            {!added ? newLineNumber : ''}
          </span>
          <span style={{ width: '20px', textAlign: 'center', marginRight: '15px', marginLeft: '5px', color: added ? '#2cbe4e' : (removed ? '#f85149' : '#6e7681') }}>
            {diffIndicator}
          </span>
          <span style={{ flex: 1, paddingLeft: '15px' }}>
            {lineContent}
          </span>
        </div>
      );

      if (!removed) oldLineNumber++;
      if (!added) newLineNumber++;
    });
  });

  return diffRows;
}