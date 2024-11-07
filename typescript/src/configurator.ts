import { OpenAI } from 'openai'
import { Store } from "./serialize/sql";
import { Provider } from './provider' // Assuming you have a Provider interface/class

/**
 * Configurator class for managing the configuration of the application.
 * 
 *
 * @class Config
 * @property {Map<string, OpenAI>} registry - The registry of OpenAI clients.
 * @property {boolean} verbose - Whether to enable verbose logging.
 * @property {boolean} wrappedLogging - Whether to enable wrapped logging.
 * @property {number | undefined} overrideWrappedLoggingWidth - The width to override wrapped logging.
 * @property {Store | undefined} store - The store for the application.
 * @property {boolean} autocommit - Whether to enable autocommit.
 * @property {boolean} lazyVersioning - Whether to enable lazy versioning.
 * @property {Record<string, any>} defaultLmParams - The default language model parameters.
 * @property {string} defaultSystemPrompt - The default system prompt.
 * @property {OpenAI | undefined} defaultClient - The default OpenAI client.
 * @property {Map<typeof OpenAI, Provider>} providers - The providers for the application.
 */
class Config {
  public registry: Map<string, OpenAI> = new Map()
  public verbose: boolean = false
  public wrappedLogging: boolean = true
  public overrideWrappedLoggingWidth?: number
  public store?: Store
  public autocommit: boolean = false
  public lazyVersioning: boolean = true
  public defaultLmParams: Record<string, any> = {}
  public defaultSystemPrompt: string = 'You are a helpful AI assistant.'
  public defaultClient?: OpenAI
  public providers: Map<typeof OpenAI, Provider> = new Map()
  private lock: any // Simulating a lock, not directly available in TypeScript

  constructor() {
    this.lock = new (require('async-lock'))()
  }

  registerModel(modelName: string, client: OpenAI): void {
    this.registry.set(modelName, client)
  }

  async modelRegistryOverride<T>(overrides: Map<string, OpenAI>, callback: () => Promise<T>): Promise<T> {
    return this.lock.acquire('registry', async () => {
      const originalRegistry = new Map(this.registry)
      this.registry = new Map([...this.registry, ...overrides])
      try {
        return await callback()
      } finally {
        this.registry = originalRegistry
      }
    })
  }

  getClientFor(modelName: string): [OpenAI | undefined, boolean] {
    let client = this.registry.get(modelName)
    let fallback = false

    if (!client) {
      const warningMessage = `Warning: A default provider for model '${modelName}' could not be found. Falling back to default OpenAI client from environment variables.`
      if (this.verbose) {
        console.warn('\x1b[33m%s\x1b[0m', warningMessage)
      } else {
        console.debug(warningMessage)
      }
      client = this.defaultClient
      fallback = true
    }

    return [client, fallback]
  }

  reset(): void {
    this.lock.acquire(['registry', 'providers'], () => {
      this.registry.clear()
      this.verbose = false
      this.wrappedLogging = true
      this.overrideWrappedLoggingWidth = undefined
      this.store = undefined
      this.autocommit = false
      this.lazyVersioning = true
      this.defaultLmParams = {}
      this.defaultSystemPrompt = 'You are a helpful AI assistant.'
      this.defaultClient = undefined
      this.providers.clear()
    })
  }

  setStore(store: Store | string, autocommit: boolean = true): void {
    if (typeof store === 'string') {
      // Assuming SQLiteStore is implemented elsewhere
      const SQLiteStore = require('./serialize/sql').SQLiteStore
      this.store = new SQLiteStore(store)
    } else {
      this.store = store
    }
    this.autocommit = autocommit || this.autocommit
  }

  getStore(): Store | undefined {
    return this.store
  }

  setDefaultLmParams(params: Record<string, any>): void {
    this.defaultLmParams = params
  }

  setDefaultSystemPrompt(prompt: string): void {
    this.defaultSystemPrompt = prompt
  }

  setDefaultClient(client: OpenAI): void {
    this.defaultClient = client
  }

  registerProvider(providerClass: Provider,clientType:any): void {
    this.lock.acquire('providers', () => {
      this.providers.set(clientType, providerClass)
    })
  }

  getProviderFor(client: OpenAI): Provider | undefined {
    for (const [key, value] of this.providers.entries()) {
      if (client instanceof key) {
        return value
      }
    }
  }
}

// Singleton instance
export const config = new Config()

// ... rest of the helper functions ...

export function init(options: {
  store?: Store | string
  verbose?: boolean
  autocommit?: boolean
  lazyVersioning?: boolean
  defaultLmParams?: Record<string, any>
  defaultSystemPrompt?: string
  defaultOpenaiClient?: OpenAI
  providers?: Array<Provider>
} = {}): void {
  config.verbose = options.verbose ?? false
  config.lazyVersioning = options.lazyVersioning ?? true

  if (options.store) {
    config.setStore(options.store, options.autocommit)
  }

  if (options.defaultLmParams) {
    config.setDefaultLmParams(options.defaultLmParams)
  }

  if (options.defaultSystemPrompt) {
    config.setDefaultSystemPrompt(options.defaultSystemPrompt)
  }

  if (options.defaultOpenaiClient) {
    config.setDefaultClient(options.defaultOpenaiClient)
  }

  // if (options.providers) {
  //   options.providers.forEach((provider) => config.registerProvider(provider))
  // }
}

// Helper functions
export const getStore = (): Store | undefined => config.getStore()
export const setStore = (store: Store | string, autocommit?: boolean): void => config.setStore(store, autocommit)
export const setDefaultLmParams = (params: Record<string, any>): void => config.setDefaultLmParams(params)
export const setDefaultSystemPrompt = (prompt: string): void => config.setDefaultSystemPrompt(prompt)

export const registerProvider = (providerClass: Provider, clientType: any): void => config.registerProvider(providerClass, clientType)
export const getProviderFor = (client: any): Provider | undefined => config.getProviderFor(client)
