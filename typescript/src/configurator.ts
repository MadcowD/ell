import { OpenAI } from "openai";
// import { Store } from "./store";
import { Provider } from "./provider"; // Assuming you have a Provider interface/class
type Store = any

class Config {
  private registry: Map<string, OpenAI> = new Map();
  public verbose: boolean = false;
  public wrappedLogging: boolean = true;
  public overrideWrappedLoggingWidth?: number;
  public store?: Store;
  public autocommit: boolean = false;
  public lazyVersioning: boolean = true;
  public defaultLmParams: Record<string, any> = {};
  public defaultSystemPrompt: string = "You are a helpful AI assistant.";
  public defaultClient?: OpenAI;
  public providers: Map<typeof OpenAI, Provider> = new Map();
  private lock: any; // Simulating a lock, not directly available in TypeScript

  constructor() {
    this.lock = new (require('async-lock'))();
  }

  registerModel(modelName: string, client: OpenAI): void {
    this.lock.acquire('registry', () => {
      this.registry.set(modelName, client);
    });
  }

  get hasStore(): boolean {
    return this.store !== undefined;
  }

  async modelRegistryOverride<T>(
    overrides: Map<string, OpenAI>,
    callback: () => Promise<T>
  ): Promise<T> {
    return this.lock.acquire('registry', async () => {
      const originalRegistry = new Map(this.registry);
      this.registry = new Map([...this.registry, ...overrides]);
      try {
        return await callback();
      } finally {
        this.registry = originalRegistry;
      }
    });
  }

  getClientFor(modelName: string): [OpenAI | undefined, boolean] {
    let client = this.registry.get(modelName);
    let fallback = false;

    if (!client) {
      const warningMessage = `Warning: A default provider for model '${modelName}' could not be found. Falling back to default OpenAI client from environment variables.`;
      if (this.verbose) {
        console.warn('\x1b[33m%s\x1b[0m', warningMessage);
      } else {
        console.debug(warningMessage);
      }
      client = this.defaultClient;
      fallback = true;
    }

    return [client, fallback];
  }

  reset(): void {
    this.lock.acquire(['registry', 'providers'], () => {
      this.registry.clear();
      this.verbose = false;
      this.wrappedLogging = true;
      this.overrideWrappedLoggingWidth = undefined;
      this.store = undefined;
      this.autocommit = false;
      this.lazyVersioning = true;
      this.defaultLmParams = {};
      this.defaultSystemPrompt = "You are a helpful AI assistant.";
      this.defaultClient = undefined;
      this.providers.clear();
    });
  }

  setStore(store: Store | string, autocommit: boolean = true): void {
    if (typeof store === 'string') {
      // Assuming SQLiteStore is implemented elsewhere
      const SQLiteStore = require('./stores/sql').SQLiteStore;
      this.store = new SQLiteStore(store);
    } else {
      this.store = store;
    }
    this.autocommit = autocommit || this.autocommit;
  }

  getStore(): Store | undefined {
    return this.store;
  }

  setDefaultLmParams(params: Record<string, any>): void {
    this.defaultLmParams = params;
  }

  setDefaultSystemPrompt(prompt: string): void {
    this.defaultSystemPrompt = prompt;
  }

  setDefaultClient(client: OpenAI): void {
    this.defaultClient = client;
  }

  registerProvider(providerClass: Provider): void {
    this.lock.acquire('providers', () => {
      this.providers.set(providerClass.getClientType(), providerClass);
    });
  }

  getProviderFor(client: OpenAI): Provider | undefined {
    for (const [key, value] of this.providers.entries()) {
      if (client instanceof key) {
        return value;
      }
    }
  }
}

// Singleton instance
export const config = new Config();

// ... rest of the helper functions ...

export function init(options: {
  store?: Store | string;
  verbose?: boolean;
  autocommit?: boolean;
  lazyVersioning?: boolean;
  defaultLmParams?: Record<string, any>;
  defaultSystemPrompt?: string;
  defaultOpenaiClient?: OpenAI;
  providers?: Array<Provider>;
}): void {
  config.verbose = options.verbose ?? false;
  config.lazyVersioning = options.lazyVersioning ?? true;

  if (options.store) {
    config.setStore(options.store, options.autocommit);
  }

  if (options.defaultLmParams) {
    config.setDefaultLmParams(options.defaultLmParams);
  }

  if (options.defaultSystemPrompt) {
    config.setDefaultSystemPrompt(options.defaultSystemPrompt);
  }

  if (options.defaultOpenaiClient) {
    config.setDefaultClient(options.defaultOpenaiClient);
  }

  if (options.providers) {
    options.providers.forEach(provider => config.registerProvider(provider));
  }
}

// Helper functions
export const getStore = (): Store | undefined => config.getStore();
export const setStore = (store: Store | string, autocommit?: boolean): void => config.setStore(store, autocommit);
export const setDefaultLmParams = (params: Record<string, any>): void => config.setDefaultLmParams(params);
export const setDefaultSystemPrompt = (prompt: string): void => config.setDefaultSystemPrompt(prompt);

export const registerProvider = (providerClass: Provider): void => config.registerProvider(providerClass);
export const getProviderFor = (client: any): Provider | undefined => config.getProviderFor(client);
