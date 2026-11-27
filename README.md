# DataLens CSV Explorer

A Streamlit app for exploring CSV files with interactive charts, summary metrics,
data-quality checks, filters, and CSV downloads. Uploaded data is processed in
the app session and is not sent to an external service.

## Run from VS Code

1. Open this folder in VS Code.
2. Select your Python environment with **Python: Select Interpreter**.
3. In the VS Code terminal, install the app dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. Start the app:

   ```powershell
   python -m streamlit run app.py
   ```

   Or use **Terminal > Run Task... > Run DataLens Streamlit app**.

Streamlit opens the dashboard in your browser. The included
`synthetic_student_support.csv` is loaded as a demo when no file is uploaded.
Use **Upload a CSV file** in the sidebar to analyze your own data.

## What it includes

- Overview metrics and a column summary
- Numeric distributions, category counts, correlation map, and relationship charts
- Category and numeric-range filters
- Missing-value, duplicate-row, and potential outlier checks
- Data preview and downloads for the filtered or original dataset
