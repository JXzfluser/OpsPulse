## Summary

<!-- What does this PR change and why? -->

## Related Issue

Closes #<!-- issue number -->

## OpsPulse checklist

- [ ] Issue Spec frontmatter is valid (`python scripts/validate-issue-spec.py <issue-file>`)
- [ ] `affected_paths` covers intended code changes
- [ ] Acceptance criteria are testable
- [ ] No secrets or `.env` files committed
- [ ] JDK 8 base image reference uses enterprise registry (not hardcoded credentials)

## Test plan

- [ ] Schema validation passes locally
- [ ] Manual review of Dockerfile / deploy config (if changed)
