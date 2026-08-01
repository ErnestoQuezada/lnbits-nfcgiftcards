# NFC Gift Cards Extension

## Installation

1. Copy the entire `nfcgiftcards` folder into your LNbits extensions directory:
   ```bash
   cp -r nfcgiftcards /path/to/lnbits/lnbits/extensions/
   ```

2. Ensure the **Withdraw** extension is enabled in LNbits.

3. Restart LNbits to register the extension and run migrations.

4. Enable "NFC Gift Cards" from the Extensions UI.

## Thumbnail

The extension tile image is referenced in `config.json` as:
```json
"tile": "/nfcgiftcards/static/nfc-gift-card.png"
```

Place any PNG image at:
```
nfcgiftcards/static/nfc-gift-card.png
```

A placeholder is included. Replace it with your own 512x512 PNG for production.

## File Structure

```
nfcgiftcards/
├── __init__.py
├── config.json
├── manifest.json
├── models.py
├── crud.py
├── migrations.py
├── views.py
├── views_api.py
├── description.md
├── toc.md
├── static/
│   ├── nfc-gift-card.png
│   └── js/
│       └── index.js
└── templates/
    └── nfcgiftcards/
        └── index.html
```

## Dependencies

- LNbits 1.5.6+
- Withdraw extension (enabled)
- Chrome on Android (for NFC writing via Web NFC API)
