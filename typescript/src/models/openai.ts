/**
 * This module handles the registration of OpenAI models within the ell framework.
 * 
 * It provides functionality to register various OpenAI models with a given OpenAI client,
 * making them available for use throughout the system. The module also sets up a default
 * client behavior for unregistered models.
 * 
 * Key features:
 * 1. Registration of specific OpenAI models with their respective types (system, openai, openai-internal).
 * 2. Utilization of a default OpenAI client for any unregistered models.
 * 
 * The default client behavior ensures that even if a specific model is not explicitly
 * registered, the system can still attempt to use it with the default OpenAI client.
 * This fallback mechanism provides flexibility in model usage while maintaining a
 * structured approach to model registration.
 * 
 * Note: The actual model availability may depend on your OpenAI account's access and the
 * current offerings from OpenAI.
 * 
 * Additionally, due to the registration of default models, the OpenAI client may be used for
 * anthropic, cohere, groq, etc. models if their clients are not registered or fail
 * to register due to an error (lack of API keys, rate limits, etc.)
 */

import { OpenAI } from 'openai';
import { config } from '../configurator';
// import { Logger } from '../logger';

const logger = console

interface ModelData {
  modelId: string;
  ownedBy: string;
}

export function register(client: OpenAI): void {
  const modelData: ModelData[] = [
    { modelId: 'gpt-4-1106-preview', ownedBy: 'system' },
    { modelId: 'gpt-4-32k-0314', ownedBy: 'openai' },
    { modelId: 'text-embedding-3-large', ownedBy: 'system' },
    { modelId: 'gpt-4-0125-preview', ownedBy: 'system' },
    { modelId: 'babbage-002', ownedBy: 'system' },
    { modelId: 'gpt-4-turbo-preview', ownedBy: 'system' },
    { modelId: 'gpt-4o', ownedBy: 'system' },   
    { modelId: 'gpt-4o-2024-05-13', ownedBy: 'system' },
    { modelId: 'gpt-4o-mini-2024-07-18', ownedBy: 'system' },
    { modelId: 'gpt-4o-mini', ownedBy: 'system' },
    { modelId: 'gpt-4o-2024-08-06', ownedBy: 'system' },
    { modelId: 'gpt-3.5-turbo-0301', ownedBy: 'openai' },
    { modelId: 'gpt-3.5-turbo-0613', ownedBy: 'openai' },
    { modelId: 'tts-1', ownedBy: 'openai-internal' },
    { modelId: 'gpt-3.5-turbo', ownedBy: 'openai' },
    { modelId: 'gpt-3.5-turbo-16k', ownedBy: 'openai-internal' },   
    { modelId: 'davinci-002', ownedBy: 'system' },
    { modelId: 'gpt-3.5-turbo-16k-0613', ownedBy: 'openai' },
    { modelId: 'gpt-4-turbo-2024-04-09', ownedBy: 'system' },
    { modelId: 'gpt-3.5-turbo-0125', ownedBy: 'system' },
    { modelId: 'gpt-4-turbo', ownedBy: 'system' },
    { modelId: 'gpt-3.5-turbo-1106', ownedBy: 'system' },
    { modelId: 'gpt-3.5-turbo-instruct-0914', ownedBy: 'system' },
    { modelId: 'gpt-3.5-turbo-instruct', ownedBy: 'system' },
    { modelId: 'gpt-4-0613', ownedBy: 'openai' },
    { modelId: 'gpt-4', ownedBy: 'openai' },
    { modelId: 'gpt-4-0314', ownedBy: 'openai' },
    { modelId: 'o1-preview', ownedBy: 'system' },
    { modelId: 'o1-mini', ownedBy: 'system' },
  ];

  modelData.forEach(({ modelId, ownedBy }) => {
    config.registerModel(modelId, client);
  });
}

let defaultClient: OpenAI | null = null;
try {
  defaultClient = new OpenAI();
} catch (e) {
  if (e instanceof Error) {
    logger.error('Failed to create default OpenAI client:', e.message);
  }
}

if (defaultClient) {
  register(defaultClient);
  config.defaultClient = defaultClient;
}