# Console Debugging

## Browser Console
Add `console.log` statements in TypeScript for debugging. They appear in browser DevTools (F12).

## Log Patterns
```typescript
// Module loading confirmation
console.log('[ModuleName] Loaded');

// Function entry with parameters
console.log('[ModuleName] functionName:', param1, param2);

// State changes
console.log('[ModuleName] State updated:', { before, after });

// Errors
console.error('[ModuleName] Error:', error.message, error);
```

## Console Interceptor
The project includes a console interceptor that:
- Prefixes all logs with source file
- Saves logs to `./logs/console.log`
- Activated automatically in development

## Viewing Logs
1. **Browser DevTools**: Press F12, go to Console tab
2. **File**: `tail -f ./logs/console.log`

## Debug Tips
- Use descriptive prefixes like `[FileTreeManager]`, `[MonacoManager]`
- Log at entry/exit of async functions
- Include relevant state in error logs
- Remove or reduce logging before committing

## Common Debug Points
```typescript
// API calls
console.log('[API] Fetching:', url);
console.log('[API] Response:', response);

// Event handlers
console.log('[Event] Click on:', element, event);

// State management
console.log('[State] Before:', this.state);
console.log('[State] After:', newState);
```
