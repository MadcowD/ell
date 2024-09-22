enum LogLevel {
  DEBUG = 10,
  INFO = 20,
  WARN = 30,
  ERROR = 40,
}

class Logger {
  private name: string;
  private level: LogLevel;

  constructor(name: string, level: LogLevel = Logger.globalLevel) {
    this.name = name;
    this.level = level;
  }

  setLevel(level: LogLevel) {
    this.level = level;
  }

  private log(level: LogLevel, message: string, data?: Record<string, any>) {
    if (this.level <= level && Logger.globalLevel <= level) {
      const levelName = LogLevel[level];
      console.log(`${levelName} - ${this.name} - ${message}`, data);
    }
  }

  debug(message: string, data?: Record<string, any>) {
    this.log(LogLevel.DEBUG, message, data);
  }

  info(message: string, data?: Record<string, any>) {
    this.log(LogLevel.INFO, message, data);
  }

  warn(message: string, data?: Record<string, any>) {
    this.log(LogLevel.WARN, message, data);
  }

  error(message: string, data?: Record<string, any>) {
    this.log(LogLevel.ERROR, message, data);
  }

  static globalLevel: LogLevel = LogLevel.INFO;

  static setGlobalLevel(level: LogLevel) {
    Logger.globalLevel = level;
  }
}

const loggers: Map<string, Logger> = new Map();

function getLogger(name: string): Logger {
  if (!loggers.has(name)) {
    loggers.set(name, new Logger(name));
  }
  return loggers.get(name)!;
}

export { Logger, LogLevel, getLogger };
