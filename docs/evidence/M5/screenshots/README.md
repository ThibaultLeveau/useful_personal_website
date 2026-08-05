# M5 responsive and theme screenshots

All captures use synthetic content from the disposable local M5 stack.

- Administrator editor and preview: `admin-experience-editor-{320,1440}.png` and
  `admin-experience-preview-{320,1440}.png`.
- Public lifecycle base captures: `public-experience-{320,1440}.png`.
- Public responsive/theme matrix: `public-experience-{320,390,768,1024,1440,1920}-{light,dark}.png`.

Playwright verified no horizontal overflow at every matrix width. Axe checks at 320 and 1440 px
reported zero violations. Integration/root visually inspected the editor, preview, base captures,
and representative 390-dark, 768-light, 1024-dark, and 1920-light images. A separate in-app browser
inspection covered the intentional empty state at 390 px dark.
