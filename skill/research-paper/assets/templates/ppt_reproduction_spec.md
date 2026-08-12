# PPT Figure Reproduction Specification

## Rights and source

- Reference image:
- Reference owner:
- Rights status: SELF_OWNED / AI_GENERATED / LICENSED / PUBLIC_DOMAIN / STRUCTURE_REDRAW_ONLY
- License or permission evidence:
- Citation required:

## GPT Image 2 reference generation

- Imagegen route: built-in / explicit CLI
- Model identity exposed by environment:
- Final prompt:
- Input image roles:
- Generated asset path:
- Transparent-background method:
- Invariants:
- Prohibited generated content: numbers / formulas / axes / topology / long text

## Canvas

- Aspect ratio:
- Reference pixels:
- PPT slide size:
- Background:
- Safe margin:

## Locked visual contract

- Main panels and order:
- Required objects:
- Required connections:
- Required text:
- Fonts:
- Palette:
- Allowed deviations:

## Layer plan

| Layer | Object | Implementation | Editable | Object ID | Notes |
|---|---|---|---|---|---|
| 0 | Background | PPT fill or licensed raster | Yes/No | | |
| 1 | Main panels | PowerPoint shapes | Yes | | |
| 2 | Scientific assets | Controlled vector or raster | Mixed | | |
| 3 | Connections | PowerPoint connectors | Yes | | |
| 4 | Text and labels | PowerPoint text | Yes | | |
| 5 | Data plots | Code-generated asset | Source available | | |

## Rendering and comparison

- Renderer and version:
- Render size:
- Resize strategy: none / stretch / contain / crop
- Pixel threshold:
- Maximum normalized MAE:
- Maximum differing-pixel ratio:
- Diff output:
- Overlay output:

## Iteration log

| Iteration | Main deviation | Single change | MAE | Differing ratio | Visual decision |
|---|---|---|---|---|---|
| 1 | | | | | |

## Final acceptance

- [ ] Source rights permit this reproduction mode
- [ ] Scientific structure verified
- [ ] All critical text is editable
- [ ] No unintended overlap or clipping
- [ ] Data plots come from controlled data/code
- [ ] PPTX opens successfully
- [ ] Render and pixel comparison completed
- [ ] Remaining deviations documented
