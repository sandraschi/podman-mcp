# Cascade Conventions & Tips

This document outlines conventions, shortcuts, and best practices for working with Cascade in the Windsurf environment.

## Table of Contents

- [Communication Style](#communication-style)
- [Common Shortenings](#common-shortenings)
- [Code References](#code-references)
- [File Operations](#file-operations)
- [Testing Conventions](#testing-conventions)
- [Documentation Tips](#documentation-tips)

## Communication Style

### Preferred Style

- Be concise but clear
- Use markdown formatting for better readability
- Reference specific files/functions using backticks
- Use emojis sparingly for emphasis

### Examples

```text
Let's fix the `calculate_stats()` function in `src/utils/math.py`.

I'll update the test cases in `tests/test_math.py` to cover edge cases.
```

## Common Shortenings

### General Communication

- `afk` - away from keyboard
- `afaik` - as far as I know
- `asap` - as soon as possible
- `b/c` - because
- `btw` - by the way
- `fyi` - for your information
- `fwiw` - for what it's worth
- `idk` - I don't know
- `iirc` - if I recall/remember correctly
- `imo`/`imho` - in my (humble) opinion
- `istr` - I seem to recall
- `jic` - just in case
- `jk` - just kidding
- `lgtm` - looks good to me
- `lmk` - let me know
- `nbd` - no big deal
- `np` - no problem
- `nvm` - never mind
- `obv` - obviously
- `omg` - oh my god
- `pbly` - probably
- `pls`/`plz` - please
- `rn` - right now
- `tbh` - to be honest
- `thx`/`tnx` - thanks
- `tldr` - too long; didn't read
- `tmi` - too much information
- `w/` - with
- `w/o` - without
- `wip` - work in progress
- `yolo` - you only live once

### Testing Terms

- `awol` - test is missing/not running
- `flaky` - test that fails intermittently
- `lgtm` - looks good to me
- `snafu` - situation normal: all fouled up
- `wontfix` - issue that won't be fixed

## Code References

### File References

```text
`src/utils/helpers.py`
```

### Function References

```text
`calculate_total()` in `src/math/operations.py`
```

### Line References

```text
See `calculate_total()` in `src/math/operations.py:42-58`
```

## File Operations

### Creating Files

```powershell
# Create new markdown file from template
.\scripts\new-md.ps1 -Path "docs/NEW_FEATURE.md" -Title "New Feature"
```

### Common Commands

```powershell
# Run markdown linter
npx markdownlint . -c .markdownlint.json

# Run tests
pytest tests/
```

## Testing Conventions

### Test Naming

- `test_` prefix for test files and functions
- Group related tests in classes
- Use descriptive test names

### Example

```python
def test_calculate_total_with_discount():
    # Test implementation
    pass
```

## Documentation Tips

### Headers

```markdown
# Main Title

## Section

### Subsection
```

### Code Blocks

````markdown
```python
def example():
    return "Hello, world!"
```
````

### Tables

```markdown
| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
| Cell 3   | Cell 4   |
```

## Best Practices

1. **Be Specific**: When reporting issues, include:
   - File paths
   - Function names
   - Line numbers
   - Error messages

2. **Use References**:

   ```text
   Let's look at `src/utils/logger.py:15-30`
   ```

3. **Keep it Organized**:
   - Group related changes together
   - One logical change per commit
   - Write clear, concise commit messages

4. **Document as You Go**:
   - Update docs when making code changes
   - Add comments for complex logic
   - Keep README files current

---

Last updated: 2025-09-12
