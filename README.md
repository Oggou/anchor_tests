# Anchor Tests (LawyerGPT) — “Shalom Aleichem”

This repo contains a small set of **anchor prompt experiments** I ran while building/iterating on “LawyerGPT”.

## What the anchor is

The anchor phrase used in these tests is:

- **Shalom Aleichem** (“peace be upon you”)

## Why it was used

The working hypothesis for this anchor is that it **shifts the framing** the model adopts, which can yield **more precise answers**:

- **Formality effect**: Hebrew (and this greeting in particular) tends to cue a more formal register.
- **Training-data prior**: “peace be upon you” appears frequently in training data (including Hebrew contexts), which may bias the model toward a more structured, cautious style.

## What’s in the repo

- `.odt` files: individual test prompts and responses (topic-by-topic).

## Notes

- This repo is **documents only** (no code).
- No API keys or credentials are intended to be stored here.

## Convert the `.odt` files to `.txt` for GitHub

GitHub can’t render `.odt` files natively. To produce plain-text versions under `text/`:

```bash
python3 convert_to_text.py
```

