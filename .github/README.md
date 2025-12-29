# GitHub Actions Workflows

This directory contains GitHub Actions workflows for SuperOpt.

## Workflows

### `deploy-docs.yml`
- **Triggers**: Push to `main` branch affecting docs files
- **Function**: Automatically builds and deploys documentation to GitHub Pages
- **Domain**: https://superagenticai.github.io/superopt/

### `test-docs.yml`
- **Triggers**: Push/PR to `main` branch affecting docs files
- **Function**: Tests documentation build without deploying

## Setup

1. Ensure `gh-pages` branch exists (created and pushed)
2. GitHub Pages should be configured to deploy from `gh-pages` branch
3. Custom domain `superopt.superagentic.ai` should be configured in repository settings

## Manual Deployment

If needed, you can manually trigger documentation deployment:

```bash
# Build locally
mkdocs build --clean

# Deploy manually (if needed)
mkdocs gh-deploy
```
