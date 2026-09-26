# MUI Rules

Generic Material UI usage rules. Version-neutral; where behavior is
version-bound, follow the latest stable MUI.

## Styling

- Prefer the `sx` prop for simple, one-off styles.
- Use MUI's `styled()` API for complex or reusable styles.
- Avoid the native `style` prop.

## Color and Theming

- Use semantic palette tokens such as `background.paper`, `background.default`,
  `text.primary`, `text.secondary`, `divider`, and `action.hover` instead of
  fixed light or dark surface colors.
- In `styled()` callbacks that build CSS values, read the active CSS-variable
  palette through `theme.vars?.palette`, with `theme.palette` only as the
  fallback for contexts that do not install the CSS-variable theme.
- Use `theme.applyStyles('light' | 'dark', ...)` when the modes intentionally
  require different declarations.
- Do not use `theme.palette.mode` to choose styles under CSS-variable theming; it
  reflects the default theme during style generation and can disagree with the
  active color scheme.
- Do not introduce a new color-scheme or theming implementation without review.

## Color Schemes

- Every new or changed UI must remain readable and visually coherent in light,
  dark, and system modes, including dialogs, menus, empty states, hover/focus
  states, and disabled controls.

## Portaled Overlays

- Before opening a `Dialog`, `Drawer`, `Modal`, `Menu`, or `Popover`, manage the
  trigger focus so MUI does not apply `aria-hidden` to an ancestor that still
  contains browser focus; restore focus on exit.
- Do not disable MUI focus enforcement.
