# Wordbee Name Streamlit Tool

A Streamlit app that generates:

1. **Wordbee Name**
2. **AEM Name** for Marketing requests only
3. **AEM URL** for each AEM Name

## Naming rules

### Wordbee Name
`GTSID_Web_FirstInitialLastName_Title_System`

- Marketing system suffix: `AEM`
- Product system suffix: `IRIS`
- If both Marketing and Product are selected, both Wordbee names are generated.

### AEM Name
`GTSID_Web_FirstInitialLastName_Title_COUNTRY`

Only generated when Marketing is selected.

### URL
The AEM URL uses the lowercase version of the AEM Name, keeps underscores, converts spaces to hyphens, removes unsafe characters, and appends it to the Thermo Fisher projects URL.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Reset behavior

The **Reset / Refresh** button clears the session and triggers a hard browser refresh.
