import { default as pino } from 'pino'
import type * as pinoPretty from 'pino-pretty'

const pinoLogger = pino({
  level: process.env.NODE_ENV === 'production' ? 'info' : 'debug',
  transport:
    process.env.NODE_ENV !== 'production'
      ? {
          target: 'pino-pretty',
          options: <pinoPretty.PrettyOptions>{
            colorize: true,
            ignore: 'pid,hostname',
            translateTime: 'SYS:standard',
          },
        }
      : undefined,
})

type LogFn = {
  (message: string, data: any, context?: Record<string, any>): void
  (data: any, context?: Record<string, any>): void
}

type LogLevel = 'info' | 'warn' | 'error' | 'debug'

type BaseLogFn = {
  (
    level: LogLevel,
    message: string,
    data: any,
    context?: Record<string, any>
  ): void
  (level: LogLevel, data: any, context?: Record<string, any>): void
}

type Logger = {
  log: BaseLogFn
  info: LogFn
  warn: LogFn
  error: LogFn
  debug: LogFn
}

export const logger: Logger = {
  log: (level: LogLevel, ...args) => {
    const message = typeof args[0] === 'string' ? args[0] : undefined
    const data = message ? args[1] : args[0]
    const context = args[2]
    if (context) {
      pinoLogger[level]({ ...context }, message, data)
    } else {
      pinoLogger[level](data, message)
    }
  },
  info: (...args) => {
    // @ts-ignore
    logger.log('info', ...args)
  },
  warn: (...args) => {
    // @ts-ignore
    logger.log('warn', ...args)
  },
  error: (...args) => {
    // @ts-ignore
    logger.log('error', ...args)
  },
  debug: (...args) => {
    // @ts-ignore
    logger.log('debug', ...args)
  },
}

logger.info('hello', { module: 'foo' })

pinoLogger.info('hello', { module: 'foo' })
