from training.data.historical_fetcher import HistoricalFetcher
from training.data.data_cleaner import DataCleaner
from training.data.dataset_builder import DatasetBuilder
import os

# Ensure output directory exists
os.makedirs("data/features", exist_ok=True)

# Define CSV file locations - they're in data/features folder
years = {
    "2020": "data/features/DAT_ASCII_EURUSD_M1_2020.csv",
    "2021": "data/features/DAT_ASCII_EURUSD_M1_2021.csv",
    "2022": "data/features/DAT_ASCII_EURUSD_M1_2022.csv"
}

# Fetch all years
all_candles = []
for year, csv_file in years.items():
    print(f"\nFetching {year}...")
    fetcher = HistoricalFetcher()
    candles = fetcher.fetch(csv_file)
    all_candles.extend(candles)
    print(f"✓ {year}: {len(candles):,} candles")

print(f"\n{'='*60}")
print(f"Total candles fetched: {len(all_candles):,}")
print(f"{'='*60}")

# Clean and build
print("\nCleaning data...")
cleaner = DataCleaner()
clean_candles = cleaner.clean(all_candles)
print(f"✓ Cleaned: {len(clean_candles):,} candles")

print("\nBuilding feature matrix (this may take several minutes)...")
builder = DatasetBuilder()
matrix = builder.build(clean_candles)
print(f"✓ Feature matrix shape: {matrix.shape}")

# Save combined dataset
print("\nSaving combined dataset...")
save_path = "data/features/eurusd_2020_2022"
builder.save(matrix, save_path)
print(f"✓ Saved to {save_path}.npy")

print(f"\n{'='*60}")
print("DATA PREPARATION COMPLETE!")
print(f"{'='*60}")
print(f"Output: {save_path}.npy")
print(f"Shape: {matrix.shape}")
print(f"Ready for training!")