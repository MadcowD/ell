# ell-ai (WIP)

This is a TypeScript/JavaScript library for interacting with the Ell API.

## Installation

```bash
npm i ell-ai
```

## Usage

```typescript
import * as ell from 'ell-ai'

const hello = ell.simple(
  { model: 'gpt-4o' },
  async (params: { firstName: string; lastName: string }) => {
    return `Say hello to ${params.firstName} ${params.lastName}!`
  }
)

const result = await hello({ firstName: 'John', lastName: 'Doe' })
```


## Runtime and module support
Ell TypeScript aims to support all JavaScript backend runtimes in addition to commonjs and ES modules.

At the time of writing Node.js has full support for versinoning and tracing.

Runtime variable capture depends on the `node:inspector` library or an equivalent. Vercel Edge runtime does not yet support this.

## Developing

Tests are currently written with two test frameworks, vitest and mocha.

Vitest does not have accurate source maps, allowing us to simulate cases where a program's source maps are not available.
There are a different set of expectations in this case, namely that the program does not blow up, but that lmps are not tracked or versioned.
These tests end in `.test.ts`.

Mocha tests use ts-node which we have found to have accurate source maps and is used for all tests that depend on them existing and being accurate.
These tests end in `.mocha.ts`.
