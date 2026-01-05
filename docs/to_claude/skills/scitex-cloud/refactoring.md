<!-- ---
!-- Timestamp: 2025-12-04 06:02:06
!-- Author: ywatanabe
!-- File: /home/ywatanabe/proj/scitex-cloud/.claude/skills/scitex-cloud/refactoring.md
!-- --- -->

# Refactoring Guidelines

## Core Principles
- **Gradual refactoring**: Prevent long files proactively during development
- **Manual only**: No bulk/regexp refactoring - small chunks, one at a time
- **Test first**: Write E2E tests before refactoring, run after each change

## File Size Limits
| Type       | Threshold  |
|------------|------------|
| TypeScript | 256 lines  |
| Python     | 256 lines  |
| CSS        | 512 lines  |
| HTML       | 1024 lines |

Check: `./scripts/check_file_sizes.sh --verbose`

## Rules

### No Inline Styles/Scripts
```html
<!-- ❌ FORBIDDEN -->
<div style="padding: 10px">
<script>doSomething()</script>

<!-- ✅ REQUIRED -->
<div class="my-component">
<script src="my-component.js"></script>
```

### TypeScript Only
- Never write JavaScript - always TypeScript
- TS auto-compiles via `tsc --watch` in Docker
- See `tsconfig/tsconfig.all.json` for config

### Commit Discipline
- Commit after each logical chunk
- Only commit when tests pass
- Clear commit messages describing the refactoring

### Edit Local Files Only
- Never edit files directly in Docker containers
- All changes must be in local project files
- Files are rsynced/volume-mounted to containers

## Refactoring Strategy

### Before Starting
1. Check current file size: `wc -l filename`
2. Write E2E tests for existing behavior
3. Identify logical extraction points

### During Refactoring
1. Extract one module/class at a time
2. Run tests after each extraction
3. Verify imports are correct
4. Commit when tests pass

### After Refactoring
1. Run `./scripts/check_file_sizes.sh --verbose`
2. Ensure all files under threshold
3. Update any affected documentation

## Current Priorities
See: `GITIGNORED/TODOS/10_CHORES_02_REFACTOR.md`

## Extraction Patterns

### TypeScript: Extract Class
```typescript
// Before: 500-line file with mixed concerns
class BigManager {
  // rendering, state, events all mixed
}

// After: Focused modules
// managers/StateManager.ts (~150 lines)
// managers/EventManager.ts (~100 lines)
// renderers/TreeRenderer.ts (~150 lines)
```

### CSS: Split by Component
```css
/* Before: 800-line monolith */
/* component.css */

/* After: Focused files */
/* component/layout.css (~200 lines) */
/* component/typography.css (~150 lines) */
/* component/animations.css (~100 lines) */
```

### HTML: Use Partials
```django
{# Before: 1200-line template #}

{# After: Include partials #}
{% include "feature/_header.html" %}
{% include "feature/_sidebar.html" %}
{% include "feature/_main.html" %}
```

<!-- EOF -->