export function cleanCode(code, customHooks) {
  const hookRanges = customHooks.map(() => []);
  const lines = code.split("\n");
  const cleanedLines = [];
  let cleanedLineIndex = 0;

  for (let index = 0; index < lines.length; index++) {
    const line = lines[index];
    let skipLine = false;

    customHooks.forEach((hook, hookIndex) => {
      if (line.includes(hook.startTag)) {
        hookRanges[hookIndex].push([cleanedLineIndex]);
        skipLine = true;
      } else if (
        line.includes(hook.endTag) &&
        hookRanges[hookIndex][hookRanges[hookIndex].length - 1]?.length === 1
      ) {
        hookRanges[hookIndex][hookRanges[hookIndex].length - 1].push(
          cleanedLineIndex - 1
        );
        const contentHook = cleanedLines
          .slice(
            hookRanges[hookIndex][hookRanges[hookIndex].length - 1][0],
            cleanedLineIndex
          )
          .join("\n");
        hookRanges[hookIndex][hookRanges[hookIndex].length - 1].push(
          contentHook
        );
        skipLine = true;
      }
    });

    if (!skipLine) {
      cleanedLines.push(line);
      cleanedLineIndex++;
    }
  }

  const cleanedCode = cleanedLines.join("\n");
  return { cleanedCode, hookRanges };
}