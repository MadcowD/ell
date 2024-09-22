import { Message, LMP } from './types'
import { config } from './configurator'
import { ELL_VERSION } from './_version'
import { createHash } from 'crypto'
import * as logging from '../_logger'

const logger = logging.getLogger('ell.verbosity')

function memoize<T extends (...args: any[]) => any>(fn: T, maxSize: number = 128): T {
  const cache = new Map<string, ReturnType<T>>()
  return function (this: any, ...args: Parameters<T>): ReturnType<T> {
    const key = JSON.stringify(args)
    if (cache.has(key)) {
      return cache.get(key)!
    }
    const result = fn.apply(this, args)
    if (cache.size >= maxSize) {
      cache.delete(cache.keys().next().value)
    }
    cache.set(key, result)
    return result
  } as T
}

// Colors and styles (using ANSI escape codes)
const ELL_COLORS = {
  RED: '\x1b[31m',
  GREEN: '\x1b[32m',
  YELLOW: '\x1b[33m',
  BLUE: '\x1b[34m',
  MAGENTA: '\x1b[35m',
  CYAN: '\x1b[36m',
  WHITE: '\x1b[37m',
} as const

const BOLD = '\x1b[1m'
const UNDERLINE = '\x1b[4m'
const RESET = '\x1b[0m'
const SYSTEM_COLOR = ELL_COLORS.CYAN
const USER_COLOR = ELL_COLORS.GREEN
const ASSISTANT_COLOR = ELL_COLORS.YELLOW
const PIPE_COLOR = ELL_COLORS.BLUE

let hasLoggedVersionStatement = false
const print = (s: string) => process.stdout.write(s + '\n')

async function checkVersionAndLog(): Promise<void> {
  if (!hasLoggedVersionStatement) {
    return
    try {
      const latestVersion = await fetch('https://docs.ell.so/_static/ell_version.txt')
        .then((r) => r.text())
        .then((text) => text.trim())
      if (latestVersion !== ELL_VERSION) {
        print(`${ELL_COLORS.YELLOW}╔═════════════════════════════════════════════════════════════════╗`)
        print(
          `${ELL_COLORS.YELLOW}║ ${ELL_COLORS.GREEN}A new version of ELL is available: ${
            ELL_COLORS.CYAN
          }${latestVersion.padEnd(29)}${ELL_COLORS.YELLOW}║`
        )
        print(
          `${ELL_COLORS.YELLOW}║ ${ELL_COLORS.GREEN}You can update by running:${ELL_COLORS.YELLOW}                                      ║`
        )
        print(
          `${ELL_COLORS.YELLOW}║ ${ELL_COLORS.CYAN}npm install ell-ai${ELL_COLORS.YELLOW}                                           ║`
        )
        print(`${ELL_COLORS.YELLOW}╚═════════════════════════════════════════════════════════════════╝${RESET}`)
      }
    } catch (error) {
      // Silently handle any network-related errors
    }
    hasLoggedVersionStatement = true
  }
}
function formatArg(arg: any, maxLength: number = 8): string {
  const strArg = String(arg)
  return strArg.length > maxLength
    ? `${ELL_COLORS.MAGENTA}${strArg.slice(0, maxLength)}..${RESET}`
    : `${ELL_COLORS.MAGENTA}${strArg}${RESET}`
}

function formatKwarg(key: string, value: any, maxLength: number = 8): string {
  const strValue = String(value)
  return `${RESET}${key}${RESET}=${ELL_COLORS.MAGENTA}${strValue.slice(
    0,
    maxLength
  )}${strValue.length > maxLength ? '..' : ''}${RESET}`
}
const computeColor = memoize((invokingLmp: LMP): string => {
  const nameHash = createHash('md5').update(invokingLmp.name).digest('hex')
  const colorIndex = parseInt(nameHash, 16) % Object.keys(ELL_COLORS).length
  return Object.values(ELL_COLORS)[colorIndex]
}, 128)

function wrapTextWithPrefix(
  text: string,
  width: number,
  prefix: string,
  subsequentPrefix: string,
  textColor: string
): string[] {
  const paragraphs = text.split('\n')
  const wrappedParagraphs = paragraphs.map(
    (p) => p.match(new RegExp(`.{1,${width - prefix.length}}(\\s+|$)`, 'g')) || [p]
  )
  const wrappedLines = wrappedParagraphs.flat()

  const result: string[] = []
  if (wrappedLines.length > 0) {
    result.push(`${prefix}${textColor}${wrappedLines[0]}${RESET}`)
    result.push(...wrappedLines.slice(1).map((line) => `${subsequentPrefix}${textColor}${line}${RESET}`))
  } else {
    result.push(`${prefix}${textColor}${RESET}`)
  }

  return result
}

function printWrappedMessages(messages: Message[], maxRoleLength: number, color: string, wrapWidth?: number): void {
  const terminalWidth = process.stdout.columns || 80
  const prefix = `${PIPE_COLOR}│   `
  const rolePrefix = ' '.repeat(maxRoleLength + 2)
  const subsequentPrefix = `${PIPE_COLOR}│   ${rolePrefix}`
  const wrappingWidth = wrapWidth || terminalWidth - prefix.length

  messages.forEach((message, i) => {
    const { role, text } = message
    const roleColor = role === 'system' ? SYSTEM_COLOR : role === 'user' ? USER_COLOR : ASSISTANT_COLOR

    const roleLine = `${prefix}${roleColor}${role.padStart(maxRoleLength)}: ${RESET}`
    const wrappedLines = wrapTextWithPrefix(
      text || '',
      wrappingWidth - rolePrefix.length,
      '',
      subsequentPrefix,
      roleColor
    )

    print(`${roleLine}${wrappedLines[0]}`)
    wrappedLines.slice(1).forEach((line) => print(line))

    if (i < messages.length - 1) {
      print(`${PIPE_COLOR}│${RESET}`)
    }
  })
}

export function modelUsageLoggerPre(
  invokingLmp: LMP,
  lmpArgs: any[],
  lmpKwargs: Record<string, any>,
  lmpHash: string,
  messages: Message[],
  color: string = '',
  argMaxLength: number = 8
): void {
  color = color || computeColor(invokingLmp)
  const formattedArgs = lmpArgs.map((arg) => formatArg(arg, argMaxLength))
  const formattedKwargs = Object.entries(lmpKwargs).map(([key, value]) => formatKwarg(key, value, argMaxLength))
  const formattedParams = [...formattedArgs, ...formattedKwargs].join(', ')

  checkVersionAndLog()

  const terminalWidth = process.stdout.columns || 80

  logger.info(`Invoking LMP: ${invokingLmp.name} (hash: ${lmpHash.slice(0, 8)})`)

  print(`${PIPE_COLOR}╔${'═'.repeat(terminalWidth - 2)}╗${RESET}`)
  print(`${PIPE_COLOR}║ ${color}${BOLD}${UNDERLINE}${invokingLmp.name}${RESET}${color}(${formattedParams})${RESET}`)
  print(`${PIPE_COLOR}╠${'═'.repeat(terminalWidth - 2)}╣${RESET}`)
  print(`${PIPE_COLOR}║ ${BOLD}Prompt:${RESET}`)
  print(`${PIPE_COLOR}╟${'─'.repeat(terminalWidth - 2)}╢${RESET}`)

  const maxRoleLength = Math.max('assistant'.length, ...messages.map((m) => m.role.length))
  printWrappedMessages(messages, maxRoleLength, color)
}

export function modelUsageLoggerPostStart(color: string = '', n: number = 1): void {
  const terminalWidth = process.stdout.columns || 80
  print(`${PIPE_COLOR}╟${'─'.repeat(terminalWidth - 2)}╢${RESET}`)
  print(`${PIPE_COLOR}║ ${BOLD}Output${n > 1 ? `[0 of ${n}]` : ''}:${RESET}`)
  print(`${PIPE_COLOR}╟${'─'.repeat(terminalWidth - 2)}╢${RESET}`)
  process.stdout.write(`${PIPE_COLOR}│   ${ASSISTANT_COLOR}assistant: ${RESET}`)
}

export function modelUsageLoggerPostIntermediate(
  color: string = '',
  n: number = 1
): (streamChunk: string, isRefusal?: boolean) => void {
  const terminalWidth = process.stdout.columns || 80
  const prefix = `${PIPE_COLOR}│   `
  const subsequentPrefix = `${PIPE_COLOR}│   ${''.padEnd('assistant: '.length)}`
  let charsPrinted = subsequentPrefix.length

  return function logStreamChunk(streamChunk: string, isRefusal: boolean = false): void {
    if (streamChunk) {
      const lines = streamChunk.split('\n')
      lines.forEach((line, i) => {
        if (charsPrinted + line.length > terminalWidth - 6) {
          process.stdout.write('\n')
          if (i === 0) {
            process.stdout.write(subsequentPrefix)
            charsPrinted = prefix.length
          } else {
            process.stdout.write(subsequentPrefix)
            charsPrinted = subsequentPrefix.length
          }
          process.stdout.write(line.trimStart())
        } else {
          process.stdout.write(line)
        }
        charsPrinted += line.length

        if (i < lines.length - 1) {
          process.stdout.write('\n')
          process.stdout.write(subsequentPrefix)
          charsPrinted = subsequentPrefix.length
        }
      })
    }
  }
}

export function modelUsageLoggerPostEnd(): void {
  const terminalWidth = process.stdout.columns || 80
  process.stdout.write(`\n${PIPE_COLOR}╚${'═'.repeat(terminalWidth - 2)}╝${RESET}`)
}

export function setLogLevel(level: string): void {
  // Implement logging level setting if needed
  console.log(`Log level set to: ${level}`)
}
