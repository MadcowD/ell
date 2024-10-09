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
