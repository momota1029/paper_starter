# Accepted repair bundle

These two changes implement the parent's accepted repair assignment after independent checks. This note records the edits, not a new audit, reader review, or test execution. The original T.md, E.md, H.md, and writer-notes.md remain immutable. No rule was changed.

## E-v2.md

Copied E.md with exactly one sentence added at the start of Overview, within its existing first paragraph:

> This fictional worked example uses synthetic session records.

Reason: `input-empirical.md` identifies the records as synthetic values for a fictional descriptive study. The added sentence makes that provenance visible to a reader of the manuscript itself. It adds no research result. All existing text, numbers, analysis, attribution, paragraph breaks, and section structure are retained.

Original E.md SHA-256: `c8679fe550369be059a483b41368670ec987cf79c6769230425fdf85635245bd`.

Revised E-v2.md SHA-256: `623237dcb7256a5bfa62079f7112097af0c83fa41f576e52369ba38aebcf4eff`.

## H-v2.md

Copied H.md with exactly one phrase replaced:

- Before: “the other four agreed”
- After: “the committee members agreed”

Reason: `input-humanities.md` separately identifies speaker V and lists five committee members as present; it does not establish that V belongs to those five. The revision removes that unsupported implication while preserving the limitation that attendance does not establish agreement. All other text, including both full quotations, attribution, and paragraph structure, is retained.

Original H.md SHA-256: `ed1e8d4b25a244851f48696b70c13603fdd174efa548abfa623742c79ffc64e8`.

Revised H-v2.md SHA-256: `49c6d5beffb25b45ce32100eef0d7881c70db890354befc76feba6d9c047bf6e`.

## Preserved files and review status

Original T.md SHA-256: `acf70f0940a33c401d6ff37c7cf8deda29f28e74c66f70d75a996e8e61bc09a6`.

Original writer-notes.md SHA-256: `f604e49d2ca6e5a9359babdb086367dedfdfc9f50426bece1685ef228c9f1411`.

Hashes were read from the local files with `sha256sum`. The parent owns independent difference review and fresh reader evaluation of these revisions. This writer authored no new audit or tests, and makes no claim that a revised-artifact review has passed. E-v2 retains the same natural line boundaries: title plus Overview, lines 1–8; Method, lines 9–16; Findings, lines 17–21.
