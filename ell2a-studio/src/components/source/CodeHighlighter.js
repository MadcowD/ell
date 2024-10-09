import React, { useCallback, useMemo } from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { atomDark as theme } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { cleanCode } from './codeCleanerUtils'
import { DiffRenderer } from './DiffRenderer'
import { StandardRenderer } from './StandardRenderer'

export function CodeHighlighter({
    code,
    previousCode,
    isDiffView,
    highlighterStyle = {},
    language = 'python',
    showLineNumbers = true,
    startingLineNumber = 1,
    customHooks = [],
    defaultRowPadding = 1,
    offset: indentOffset = 35
}) {
    const { cleanedCode, hookRanges } = useMemo(() => cleanCode(code, customHooks), [code, customHooks])
    const commonProps = useMemo(() => {
        return {
            language,
            style: theme,
            customStyle: {
                margin: 0,
                padding: '1em',
                borderRadius: '0 0 6px 6px',
                ...highlighterStyle
            }
        }
    }, [language, highlighterStyle])

    const standardRenderer = useCallback(
        ({ rows, stylesheet, useInlineStyles }) =>
            StandardRenderer({
                rows,
                stylesheet,
                useInlineStyles,
                customHooks,
                hookRanges,
                indentOffset,
                defaultRowPadding
            }),
        [customHooks, hookRanges, indentOffset, defaultRowPadding]
    )

    const diffRenderer = useCallback(
        ({ stylesheet, useInlineStyles }) =>
            DiffRenderer({
                previousCode: previousCode,
                code: code,
                stylesheet,
                useInlineStyles,
                startingLineNumber,
                commonProps
            }),
        [previousCode, code, startingLineNumber, commonProps]
    )

    if (isDiffView && previousCode && code) {
        return (
            <SyntaxHighlighter {...commonProps} showLineNumbers={false} renderer={diffRenderer} language="python">
                {''}
            </SyntaxHighlighter>
        )
    }

    return (
        <SyntaxHighlighter
            {...commonProps}
            showLineNumbers={showLineNumbers}
            startingLineNumber={startingLineNumber}
            wrapLines
            renderer={standardRenderer}>
            {cleanedCode}
        </SyntaxHighlighter>
    )
}
