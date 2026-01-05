# Django Full-Stack Organization

## Core Principle
**1:1:1:1 correspondence** across the entire stack:
```
Frontend:  HTML ←→ CSS ←→ TypeScript
Backend:   View ←→ Service ←→ Model
```

Every feature has corresponding files at every layer.

## Directory Structure
```
apps/
└── {app_name}/
    ├── templates/{app_name}/
    │   ├── {feature}.html
    │   └── {feature}_partials/
    │       └── _{component}.html
    ├── static/{app_name}/
    │   ├── css/{feature}/
    │   │   └── {component}.css
    │   └── ts/{feature}/
    │       └── {component}.ts
    ├── views/
    │   └── {feature}/
    │       ├── __init__.py
    │       └── api/
    │           └── {endpoint}.py
    └── services/
        └── {feature}_service.py
```

## No Inline Styles
**FORBIDDEN**: `style="padding: 10px"` in HTML/TypeScript

**REQUIRED**: CSS classes for all styling

For dynamic styles, use `<style>` blocks:
```typescript
// Good: CSS classes + dynamic <style>
let css = '<style>';
css += `.col-${i} { width: ${width}px; }`;
css += '</style>';
```

## URL Patterns
```python
# Feature-based URLs
path('{feature}/', include([
    path('', views.index, name='{feature}'),
    path('api/', include([
        path('{action}/', views.api.action, name='{feature}-{action}'),
    ])),
])),
```

## Naming Conventions
- Templates: `{feature}.html`, `_{partial}.html`
- CSS: `{feature}.css`, `{component}.css`
- TypeScript: `{Feature}.ts`, `{Component}.ts`
- Views: `{feature}_views.py` or `views/{feature}/`
- Services: `{feature}_service.py`
