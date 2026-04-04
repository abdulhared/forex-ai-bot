from training.data.historical_fetcher import HistoricalFetcher
from training.data.data_cleaner import DataCleaner
from training.data.dataset_builder import DatasetBuilder
import os

# Ensure output directory exists
os.makedirs("data/features", exist_ok=True)

# Process each year
years = {
    "2020": "DAT_ASCII_EURUSD_M1_2020.csv",
    "2021": "DAT_ASCII_EURUSD_M1_2021.csv",
    "2022": "DAT_ASCII_EURUSD_M1_2022.csv"
}

for year, csv_file in years.items():
    print(f"\n{'='*60}")
    print(f"Processing {year}")
    print(f"{'='*60}")
    
    # Step 1: Fetch (M1 → M15)
    fetcher = HistoricalFetcher()
    candles = fetcher.fetch(csv_file)
    print(f"✓ Fetched {len(candles):,} M15 candles")
    
    # Step 2: Clean
    cleaner = DataCleaner()
    clean_candles = cleaner.clean(candles)
    print(f"✓ Cleaned {len(clean_candles):,} candles")
    
    # Step 3: Build features
    builder = DatasetBuilder()
    matrix = builder.build(clean_candles)
    print(f"✓ Feature matrix: {matrix.shape}")
    
    # Step 4: Save
    save_path = f"data/features/eurusd_{year}"
    builder.save(matrix, save_path)
    print(f"✓ Saved to {save_path}.npy")