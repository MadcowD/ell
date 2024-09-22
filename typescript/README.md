# ell-ai (WIP)

This is a TypeScript/JavaScript library for interacting with the Ell API.

## Installation

```bash
npm install ell-ai
```

## Usage

```typescript
import * as ell from 'ell-ai'

const hello = ell.simple(
  { model: 'gpt-4o' },
  async (params: { firstName: string; lastName: string }) => {
    await fetch('')
  }
)

const result = await hello({ firstName: 'John', lastName: 'Doe' })
```
