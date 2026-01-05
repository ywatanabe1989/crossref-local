# Vite HMR

Edit `.ts` → Vite detects → HMR to browser (~200ms)

## Template
```html
{% load vite %}
{% vite_hmr_client %}
{% vite_script 'code_app/workspace' %}
```

## Config
- `vite.config.ts` - Entry points, path resolution
- Entry: `{app}/name` → `apps/{app}/static/{app}/ts/name.ts`

## Troubleshooting
```bash
# Vite logs
tail -f ./logs/vite-dev.log

# Restart
make env=dev restart
```
