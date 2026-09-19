# KrishiDisha — Raw Dataset Dropzone
Place your raw agricultural dataset CSV files here (e.g. from Kaggle or data.gov.in).

### Expected Data:
- Historical APMC/Agmarknet mandi commodity prices
- Columns typically include: State, District, Market/Mandi, Commodity, Variety, Grade, Arrival_Date, Min_Price, Max_Price, Modal_Price, Arrivals_Tonnes.

The ML & Data Pipeline Agent will ingest raw files from this directory, preprocess them into `data/processed/`, train the XGBoost forecasting model, and the Backend Agent will ingest them into PostgreSQL tables (`markets`, `commodities`, `market_prices`).
