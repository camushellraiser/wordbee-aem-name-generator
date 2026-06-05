# Wordbee Name Generator

Streamlit tool for pasted AEM rows.

## Workflow
1. Copy one or more rows from AEM.
2. Paste the copied text into the big text box.
3. Select Marketing, Product, or both.
4. Select one or more countries when Marketing is enabled.

## Outputs
- Wordbee Name
- AEM Name for each selected country when Marketing is selected
- AEM URL for each generated AEM Name

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Notes
- The parser is designed for pasted AEM selections with tabs, wrapped lines, or multiple rows.
- Product-only requests skip AEM Name generation.
- The Reset / Refresh button performs a full page reload.
