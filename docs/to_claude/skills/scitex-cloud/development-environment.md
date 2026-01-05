# Development Environment

## Docker-Based Development
All development runs in Docker containers. Never run Django directly on host.

## Start/Stop Commands
```bash
# Start development
make env=dev start

# Stop
make env=dev stop

# Restart
make env=dev restart

# Status
make env=dev status
```

## Container Names
- `scitex-cloud-dev-django-1` - Main Django app
- `scitex-cloud-dev-postgres-1` - PostgreSQL database
- `scitex-cloud-dev-redis-1` - Redis cache
- `scitex-cloud-dev-gitea-1` - Git hosting
- `scitex-cloud-dev-celery_worker-1` - Background tasks
- `scitex-cloud-dev-celery_beat-1` - Scheduled tasks

## Running Django Commands
```bash
# Migrations
docker exec scitex-cloud-dev-django-1 python manage.py migrate --settings=config.settings.settings_dev

# Shell
docker exec -it scitex-cloud-dev-django-1 python manage.py shell --settings=config.settings.settings_dev

# Create superuser
docker exec -it scitex-cloud-dev-django-1 python manage.py createsuperuser --settings=config.settings.settings_dev
```

## Hot Reload
- **Django**: Auto-reloads on Python file changes
- **TypeScript**: Auto-compiles on `.ts` file changes
- **Templates**: Auto-reloads via django-browser-reload
- **CSS**: Auto-refreshes via WhiteNoise

## Access URLs
- Main app: http://127.0.0.1:8000
- Gitea: http://127.0.0.1:3000
- Flower (Celery): http://127.0.0.1:5555

## Environment Files
- `SECRET/.env.dev` - Development environment variables
- `SECRET/.env.nas` - NAS production environment

## Test User
For testing: `test-user` / `Password123!`
