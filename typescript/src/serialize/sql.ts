import * as fs from 'fs'
import * as path from 'path'
import * as zlib from 'zlib'
import { promisify } from 'util'
import * as sqlite3 from 'sqlite3'
import { open, Database } from 'sqlite'
import { LMPType } from '../lmp/types'

const gzip = promisify(zlib.gzip)
const gunzip = promisify(zlib.gunzip)

export type ISODateString = string

export function utcNow(): ISODateString {
  return new Date().toISOString()
}

// SQL model types

type SerializedLmpUses = {
  lmp_user_id: string
  lmp_using_id: string
}
const SerializedLmpUses = (props: SerializedLmpUses) => props

type SerializedLmp = {
  lmp_id: string
  name: string
  source: string
  dependencies: string
  created_at: Date
  lmp_type: LMPType
  api_params: Record<string, any>
  initial_free_vars: Record<string, any>
  initial_global_vars: Record<string, any>
  num_invocations: number
  commit_message: string
  version_number: number
  invocations: Invocation[]
  used_by: SerializedLmp[]
  uses: SerializedLmp[]
}
const SerializedLmp = (props: SerializedLmp) => props

type InvocationTrace = {
  invocation_consumer_id: string
  invocation_consuming_id: string
}
const InvocationTrace = (props: InvocationTrace) => props

export type Invocation = {
  id: string
  lmp_id: string
  latency_ms: number
  prompt_tokens: number
  completion_tokens: number
  state_cache_key: string
  created_at: ISODateString
  used_by_id: string
  lmp: SerializedLmp
  consumed_by: Invocation[]
  consumes: Invocation[]
  used_by: Invocation | null
  uses: Invocation[]
  contents: InvocationContents
}
export const Invocation = (props: Invocation) => props

export type InvocationContents = {
  invocation_id: string
  params: Record<string, any>
  results: any
  invocation_api_params: Record<string, any>
  global_vars: Record<string, any>
  free_vars: Record<string, any>
  is_external: boolean
  invocation: Invocation
}
export const InvocationContents = (props: InvocationContents) => ({
  ...props,
  get should_externalize(): boolean {
    const jsonFields = [this.params, this.results, this.invocation_api_params, this.global_vars, this.free_vars]
    const totalSize = jsonFields
      .filter((field) => field !== null)
      .reduce((sum, field) => sum + JSON.stringify(field).length, 0)
    return totalSize > 102400 // Precisely 100kb in bytes
  },
})

export interface BlobStore {
  storeBlob(blob: Uint8Array, blobId: string): Promise<string>
  retrieveBlob(blobId: string): Promise<Uint8Array>
}

export abstract class Store {
  protected blobStore?: BlobStore

  constructor(blobStore?: BlobStore) {
    this.blobStore = blobStore
  }

  get hasBlobStorage(): boolean {
    return this.blobStore !== undefined
  }

  abstract writeLMP(input: WriteLMPInput): Promise<any | undefined>

  abstract writeInvocation(input: WriteInvocationInput): Promise<any | undefined>

  abstract getVersionsByFqn(fqn: string): Promise<SerializedLmp[]>

  //   abstract getCachedInvocationsAsync(lmpId: string, stateCacheKey: string): Promise<Invocation[]>

  //   async freeze(...lmps: InvocableLM[]): Promise<void> {
  //     const oldCacheValues = new Map<InvocableLM, any>()

  //     try {
  //       for (const lmp of lmps) {
  //         oldCacheValues.set(lmp, (lmp as any).__ell_use_cache__)
  //         ;(lmp as any).__ell_use_cache__ = this
  //       }
  //       // Yield equivalent in TypeScript would be to return a Promise
  //       // that resolves immediately
  //       await Promise.resolve()
  //     } finally {
  //       // TODO: Implement cache storage logic here
  //       for (const lmp of lmps) {
  //         if (oldCacheValues.has(lmp)) {
  //           ;(lmp as any).__ell_use_cache__ = oldCacheValues.get(lmp)
  //         } else {
  //           delete (lmp as any).__ell_use_cache__
  //         }
  //       }
  //     }
  //   }
}

export class SQLiteStore extends Store {
  private db: Database | null = null
  private dbPath: string

  constructor(dbDir: string) {
    if (dbDir === ':memory:') {
      const blobStore = new SQLBlobStore(dbDir)
      super(blobStore)
      this.dbPath = ':memory:'
    } else {
      if (dbDir.endsWith('.db')) {
        throw new Error('Create store with a directory not a db.')
      }
      fs.mkdirSync(dbDir, { recursive: true })
      const blobStore = new SQLBlobStore(dbDir)
      super(blobStore)
      this.dbPath = path.join(dbDir, 'ell.db')
    }
  }

  async initialize(): Promise<void> {
    this.db = await open({
      filename: this.dbPath,
      driver: sqlite3.Database,
    })

    await this.createTables()
  }

  private async createTables(): Promise<void> {
    await this.db!.exec(`
        CREATE TABLE IF NOT EXISTS serialized_lmp (
          lmp_id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          source TEXT NOT NULL,
          dependencies TEXT NOT NULL,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          lmp_type TEXT NOT NULL,
          api_params TEXT,
          initial_free_vars TEXT,
          initial_global_vars TEXT,
          num_invocations INTEGER DEFAULT 0,
          commit_message TEXT,
          version_number INTEGER
        );
  
        CREATE TABLE IF NOT EXISTS invocation (
          id TEXT PRIMARY KEY,
          lmp_id TEXT NOT NULL,
          latency_ms REAL NOT NULL,
          prompt_tokens INTEGER,
          completion_tokens INTEGER,
          state_cache_key TEXT,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          used_by_id TEXT,
          FOREIGN KEY (lmp_id) REFERENCES serialized_lmp (lmp_id)
        );
  
        CREATE TABLE IF NOT EXISTS invocation_trace (
          invocation_consumer_id TEXT NOT NULL,
          invocation_consuming_id TEXT NOT NULL,
          PRIMARY KEY (invocation_consumer_id, invocation_consuming_id),
          FOREIGN KEY (invocation_consumer_id) REFERENCES invocation (id),
          FOREIGN KEY (invocation_consuming_id) REFERENCES invocation (id)
        );
  
        CREATE TABLE IF NOT EXISTS invocation_contents (
          invocation_id TEXT PRIMARY KEY,
          params TEXT,
          results TEXT,
          invocation_api_params TEXT,
          global_vars TEXT,
          free_vars TEXT,
          is_external BOOLEAN DEFAULT FALSE,
          FOREIGN KEY (invocation_id) REFERENCES invocation (id)
        );
  
        CREATE TABLE IF NOT EXISTS serialized_lmp_uses (
          lmp_user_id TEXT NOT NULL,
          lmp_using_id TEXT NOT NULL,
          PRIMARY KEY (lmp_user_id, lmp_using_id),
          FOREIGN KEY (lmp_user_id) REFERENCES serialized_lmp (lmp_id),
          FOREIGN KEY (lmp_using_id) REFERENCES serialized_lmp (lmp_id)
        );
      `)

    // Create indexes
    await this.db!.exec(`
        CREATE INDEX IF NOT EXISTS idx_serialized_lmp_name ON serialized_lmp (name);
        CREATE INDEX IF NOT EXISTS idx_serialized_lmp_created_at ON serialized_lmp (created_at);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_serialized_lmp_version_name ON serialized_lmp (version_number, name);
        CREATE INDEX IF NOT EXISTS idx_invocation_lmp_id_created_at ON invocation (lmp_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_invocation_created_at_latency ON invocation (created_at, latency_ms);
        CREATE INDEX IF NOT EXISTS idx_invocation_created_at_tokens ON invocation (created_at, prompt_tokens, completion_tokens);
      `)
  }

  async writeLMP(input: WriteLMPInput): Promise<any | undefined> {
    const {
      lmp_id,
      name,
      source,
      dependencies,
      lmp_type,
      api_params,
      initial_free_vars,
      initial_global_vars,
      commit_message,
      version_number,
      uses,
    } = input
    await this.db!.run('BEGIN TRANSACTION')

    try {
      await this.db!.run(
        `
          INSERT OR REPLACE INTO serialized_lmp 
          (lmp_id, name, source, dependencies, lmp_type, api_params, initial_free_vars, initial_global_vars, commit_message, version_number)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        `,
        [
          lmp_id,
          name,
          source,
          dependencies,
          lmp_type,
          JSON.stringify(api_params),
          JSON.stringify(initial_free_vars),
          JSON.stringify(initial_global_vars),
          commit_message,
          version_number,
        ]
      )

      for (const useId of Object.keys(uses)) {
        await this.db!.run(
          `
            INSERT OR IGNORE INTO serialized_lmp_uses (lmp_user_id, lmp_using_id)
            VALUES (?, ?)
          `,
          [lmp_id, useId]
        )
      }
    } catch (error) {
      await this.db!.run('ROLLBACK')
      throw error
    }

    await this.db!.run('COMMIT')

    return undefined
  }

  async writeInvocation(input: WriteInvocationInput): Promise<any | undefined> {
    // Start a transaction
    await this.db!.run('BEGIN TRANSACTION')

    try {
      // Update the num_invocations for the associated LMP
      await this.db!.run(
        `
        UPDATE serialized_lmp
        SET num_invocations = num_invocations + 1
        WHERE lmp_id = ?
      `,
        [input.lmp_id]
      )

      // Insert the invocation record
      await this.db!.run(
        `
        INSERT INTO invocation (
          id, lmp_id, latency_ms, prompt_tokens, completion_tokens, 
          state_cache_key, created_at, used_by_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      `,
        [
          input.invocation_id,
          input.lmp_id,
          input.latency_ms,
          input.prompt_tokens,
          input.completion_tokens,
          input.state_cache_key,
          input.created_at,
          input.used_by_id,
        ]
      )

      // Insert invocation contents
      if (input.contents) {
        await this.db!.run(
          `
          INSERT INTO invocation_contents (
            invocation_id, params, results, invocation_api_params,
            global_vars, free_vars, is_external
          ) VALUES (?, ?, ?, ?, ?, ?, ?)
        `,
          [
            input.invocation_id,
            JSON.stringify(input.contents.params),
            JSON.stringify(input.contents.results),
            JSON.stringify(input.contents.invocation_api_params),
            JSON.stringify(input.contents.global_vars),
            JSON.stringify(input.contents.free_vars),
            input.contents.is_external ? 1 : 0,
          ]
        )
      }

      // Insert invocation traces
      for (const consumedId of input.consumes) {
        await this.db!.run(
          `
          INSERT INTO invocation_trace (invocation_consumer_id, invocation_consuming_id)
          VALUES (?, ?)
        `,
          [input.invocation_id, consumedId]
        )
      }

      // Commit the transaction
      await this.db!.run('COMMIT')

      return undefined
    } catch (error) {
      // If there's an error, roll back the transaction
      await this.db!.run('ROLLBACK')
      throw error
    }
  }

  /**
   * Get all versions of an LMP by its fully qualified name.
   *
   * Note: This is only used in TypeScript to increment the version number.
   * So we return an abbreviated version of the SerializedLmp object that does not include all joins.
   * @param fqn - The fully qualified name of the LMP.
   * @returns A promise that resolves to an array of SerializedLmp objects.
   */
  async getVersionsByFqn(fqn: string): Promise<SerializedLmp[]> {
    const rows = await this.db!.all(
      `
      SELECT 
        lmp_id, name, source, dependencies, created_at, lmp_type,
        api_params, initial_free_vars, initial_global_vars,
        num_invocations, commit_message, version_number
      FROM serialized_lmp
      WHERE name = ?
      ORDER BY version_number DESC
    `,
      [fqn]
    )

    return rows.map((row) => ({
      lmp_id: row.lmp_id,
      name: row.name,
      source: row.source,
      dependencies: row.dependencies,
      created_at: new Date(row.created_at),
      lmp_type: row.lmp_type,
      api_params: JSON.parse(row.api_params),
      initial_free_vars: JSON.parse(row.initial_free_vars),
      initial_global_vars: JSON.parse(row.initial_global_vars),
      num_invocations: row.num_invocations,
      commit_message: row.commit_message,
      version_number: row.version_number,
      // These are not provided or needed for TypeScript currently
      invocations: [],
      used_by: [],
      uses: [],
    }))
  }
}

export class SQLBlobStore implements BlobStore {
  private dbDir: string

  constructor(dbDir: string) {
    this.dbDir = dbDir
  }

  async storeBlob(blob: Uint8Array, blobId: string): Promise<string> {
    const filePath = this.getBlobPath(blobId)
    fs.mkdirSync(path.dirname(filePath), { recursive: true })
    const compressedBlob = await gzip(blob)
    fs.writeFileSync(filePath, compressedBlob)
    return blobId
  }

  async retrieveBlob(blobId: string): Promise<Uint8Array> {
    const filePath = this.getBlobPath(blobId)
    const compressedBlob = fs.readFileSync(filePath)
    return gunzip(compressedBlob)
  }

  private getBlobPath(id: string, depth: number = 2): string {
    if (!id.includes('-')) {
      throw new Error('Blob id must have a single - in it to split on.')
    }
    const [type, _id] = id.split('-')
    const increment = 2
    const dirs = [type, ...[...Array(depth)].map((_, i) => _id.slice(i * increment, (i + 1) * increment))]
    const fileName = _id.slice(depth * increment)
    return path.join(this.dbDir, ...dirs, fileName)
  }
}

// API types

export type WriteLMPInput = {
  lmp_id: string
  name: string
  source: string
  dependencies: string
  created_at: ISODateString
  lmp_type: LMPType
  api_params: Record<string, any>
  initial_free_vars: Record<string, any>
  initial_global_vars: Record<string, any>
  commit_message: string
  version_number: number
  uses: string[]
}

export type WriteInvocationContentsInput = {
  params: Record<string, any>
  results: any
  invocation_api_params: Record<string, any>
  global_vars: Record<string, any>
  free_vars: Record<string, any>
  is_external?: boolean
}

export type WriteInvocationInput = {
  id: string
  lmp_id: string
  latency_ms: number
  prompt_tokens: number
  completion_tokens: number
  state_cache_key: string
  created_at: ISODateString
  used_by_id: string | undefined
  contents: WriteInvocationContentsInput
  consumes: string[]
}
