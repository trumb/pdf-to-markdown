# Release Process

Release workflow for PDF-to-Markdown.

## Version Numbering

We use [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking API changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

Example: `1.2.3` → Major.Minor.Patch

## Pre-Release Checklist

- [ ] All tests passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped in pyproject.toml
- [ ] Security review complete
- [ ] Performance testing done

## Release Steps

```bash
# 1. Update version
# Edit pyproject.toml: version = "1.0.0"

# 2. Update CHANGELOG.md
# Add release notes under [1.0.0] section

# 3. Commit changes
git add .
git commit -m "chore: release v1.0.0"

# 4. Create tag
git tag -a v1.0.0 -m "Release v1.0.0"

# 5. Push
git push origin main
git push origin v1.0.0

# 6. GitHub Actions will:
# - Run tests
# - Build Docker image
# - Create GitHub Release
# - Publish to PyPI (if configured)
```

## Post-Release

- [ ] Verify GitHub Release created
- [ ] Test Docker image
- [ ] Update documentation site
- [ ] Announce release
- [ ] Monitor for issues

## Hotfix Process

For critical bugs in production:

```bash
# 1. Create hotfix branch from tag
git checkout -b hotfix/1.0.1 v1.0.0

# 2. Fix bug and test
# Make changes
pytest

# 3. Update version (patch bump)
# Edit pyproject.toml: version = "1.0.1"

# 4. Commit and tag
git commit -am "fix: critical bug description"
git tag -a v1.0.1 -m "Hotfix v1.0.1"

# 5. Push
git push origin hotfix/1.0.1
git push origin v1.0.1

# 6. Merge back to main
git checkout main
git merge hotfix/1.0.1
git push origin main
```

See [CHANGELOG.md](../../CHANGELOG.md) for release history.