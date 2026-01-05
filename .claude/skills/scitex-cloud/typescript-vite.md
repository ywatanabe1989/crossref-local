# TypeScript with Vite

**DO NOT run `tsc` manually** - Vite handles all TypeScript.

## Imports
```typescript
// Use .ts extension (not .js)
import { helper } from "./utils/helper.ts";

// Cross-app: /static/{app}/ts/...
import { modal } from "/static/writer_app/ts/modules/modal.ts";
```

## Verify Vite Running
```bash
tail -f ./logs/vite-dev.log
```
