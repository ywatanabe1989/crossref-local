<!-- ---
!-- Timestamp: 2025-12-04 06:03:23
!-- Author: ywatanabe
!-- File: /home/ywatanabe/.claude/to_claude/skills/scitex-cloud/SKILL.md
!-- --- -->

---
name: project-specific
description: SciTeX Cloud project-specific guidelines. Use when working on this Django/TypeScript web application. Covers TypeScript compilation, Django organization, and development workflows.
---

# SciTeX Cloud Project-Specific Guidelines

## When to Use
- Working on SciTeX Cloud web application
- Editing TypeScript or Django files
- Debugging frontend/backend issues
- Understanding project structure

## TypeScript Development
**Critical: TypeScript watch runs automatically in Docker. NEVER run `tsc` manually.**
**Error detection: Check `TYPESCRIPT_ERRORS.log` in project root for compilation errors.**
@typescript-watch.md

## Django Organization
Full-stack organization with 1:1:1:1 correspondence:
@django-organization.md

## Development Environment
Docker-based development with hot-reload:
@development-environment.md

## Console Debugging
Browser console logging for frontend debugging:
@console-debugging.md

## Refactoring
Django refactoring guide for maintainability
@refactoring.md

<!-- EOF -->