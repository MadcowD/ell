import React from 'react';
import { createElement } from "react-syntax-highlighter";

export function StandardRenderer({
  rows,
  stylesheet,
  useInlineStyles,
  customHooks,
  hookRanges,
  indentOffset,
  defaultRowPadding
}) {
  const rowTree = [];
  const activeHooks = customHooks.map(() => null);

  for (let i = 0; i < rows.length; i++) {
    let currentElement = (
      <div
        style={{
          paddingLeft: `${indentOffset + defaultRowPadding}px`,
          textIndent: `-${indentOffset}px`,
        }}
        key={i}
      >
        {createElement({
          node: rows[i],
          stylesheet,
          useInlineStyles,
          key: `code-segment-${i}`,
        })}
      </div>
    );

    for (let hookIndex = 0; hookIndex < customHooks.length; hookIndex++) {
      const hook = customHooks[hookIndex];

      const containingInterval = hookRanges[hookIndex].some(
        ([start, end, _]) => start <= i && i <= end
      );
      if (containingInterval) {
        if (activeHooks[hookIndex] === null) {
          activeHooks[hookIndex] = [];
        }
        activeHooks[hookIndex].push(currentElement);
        currentElement = null;
      } else if (activeHooks[hookIndex] !== null) {
        const rangeOfLastHook = hookRanges[hookIndex].find(
          ([start, end, contents]) => start <= i - 1 && i - 1 <= end
        );

        rowTree.push(
          hook.wrapper({
            children: activeHooks[hookIndex],
            content: rangeOfLastHook[2],
            key: `${hook.name}-${i}`,
          })
        );
        activeHooks[hookIndex] = null;
      }
    }

    if (currentElement) {
      rowTree.push(currentElement);
    }
  }

  customHooks.forEach((hook, hookIndex) => {
    if (activeHooks[hookIndex] !== null) {
      const range = hookRanges[hookIndex][hookRanges[hookIndex].length - 1];

      rowTree.push(
        hook.wrapper({
          children: activeHooks[hookIndex],
          key: `${hook.name}-end`,
          content: range[2],
        })
      );
    }
  });

  return rowTree;
}