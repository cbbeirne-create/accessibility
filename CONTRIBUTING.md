# Contributing

Thanks for wanting to contribute to Auditly. These guidelines help us keep the codebase healthy and make reviews faster.

## How to contribute
- Fork the repo and open a branch named using this pattern: `feat/<short-desc>`, `fix/<short-desc>`, `docs/<short-desc>`, or `chore/<short-desc>`.
- Keep changes small and focused. One logical change per PR makes reviews faster.
- Write clear commit messages (use present-tense imperative): e.g. `fix: validate scan URL before enqueue`.

## Development workflow
1. Pull the latest main: `git checkout main && git pull origin main`.
2. Create a branch: `git checkout -b feat/add-backend-readme`.
3. Run tests locally before committing (see below).
4. Push your branch and open a Pull Request against `main`.

## Pull Request checklist
- [ ] PR description explains the intent and any user-visible changes.
- [ ] All new and existing tests pass locally.
- [ ] Update or add documentation where applicable (README, DEPLOYMENT.md, API docs).
- [ ] No secrets or credentials are included in the changes.
- [ ] Linting/formatting applied (Black / Prettier where configured).

## Tests
- Backend: `cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && pytest -q`
- Frontend: `cd frontend && yarn install && yarn test`

## Coding standards
- Python: follow PEP8. Use Black for formatting, and Flake8 for linting if configured.
- JavaScript/React: follow project's ESLint/Prettier configuration (if present).

## Reviewing and merging
- PRs should have at least one approval from a maintainer. Maintainters will squash/merge using the PR title as the resulting commit message where appropriate.
- Rebase or resolve merge conflicts locally before merging.

## Reporting issues
- Use the repository Issues to report bugs or request features. Provide steps to reproduce and any relevant logs or screenshots.

## Code of Conduct
Be respectful and constructive in all interactions.

---
If you'd like, I can also add a basic GitHub Actions workflow to run backend tests and frontend tests on PRs, and create issue/PR templates. Would you like me to add those next?