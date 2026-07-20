# Markdown Style Guide

## Table of Contents

- [Headings](#headings)
- [Paragraphs and Line Breaks](#paragraphs-and-line-breaks)
- [Lists](#lists)
- [Code Blocks](#code-blocks)
- [Links and Images](#links-and-images)
- [Tables](#tables)
- [Emphasis](#emphasis)
- [Best Practices](#best-practices)

## Headings

Use ATX-style headings with closing hashes for consistency:

```markdown
# H1
## H2
### H3
#### H4
```

## Paragraphs and Line Breaks

- Use a single blank line between paragraphs
- Do not use multiple consecutive blank lines
- End each sentence with a single space

## Lists

### Ordered Lists

1. First item
2. Second item
3. Third item

### Unordered Lists

- Item 1
- Item 2
  - Nested item 2a
  - Nested item 2b

## Code Blocks

Use fenced code blocks with language specification:

```python
def hello_world():
    print("Hello, world!")
```

For inline code, use single backticks: `example`.

## Links and Images

### Links

[Example Link](https://example.com)

### Images

![Alt text](/path/to/image.jpg)

## Tables

| Header 1 | Header 2 |
|----------|----------|
| Row 1    | Data     |
| Row 2    | Data     |

## Emphasis

- **Bold** for strong emphasis
- *Italic* for subtle emphasis
- ***Bold and Italic*** for strong emphasis with subtlety
- ~~Strikethrough~~ for removed content

## Best Practices

1. Keep lines under 120 characters
2. Use consistent indentation (spaces, not tabs)
3. Always add alt text for images
4. Use semantic line breaks for better diffing
5. Keep headings properly nested
6. Use relative links for internal documentation
7. Always include a table of contents for long documents
8. Use reference-style links for better readability

## Example of a Well-Formatted Document

Here's how to properly format a markdown document:

1. Start with a main heading
2. Add sections with appropriate subheadings
3. Include lists, code blocks, and other elements with proper spacing

### Code Block Example

```python
def example():
    return "This is a properly formatted code block"
```

### Complete Document Example

For a complete example, see the following markdown document:

````markdown
# Document Title

## Section 1

This is a well-formatted paragraph that demonstrates proper line length and wrapping. It stays under 120 characters per line for better readability.

### Subsection

- List item 1
- List item 2
  - Nested item

```python
def example():
    return "This is a code block with proper indentation"
```

[Learn more about Markdown](https://www.markdownguide.org/)
````

Note: The above example shows how to properly nest a markdown code block within another markdown document.
