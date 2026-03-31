from training.data.historical_fetcher import HistoricalFetcher
from training.data.data_cleaner import DataCleaner
from training.data.dataset_builder import DatasetBuilder
import os

# Create features directory if it doesn't exist
os.makedirs("data/features", exist_ok=True)

# Step 1 — fetch
fetcher = HistoricalFetcher()
candles = fetcher.fetch(r"C:\Users\abdul\OneDrive\Desktop\DAT_ASCII_EURUSD_M1_2020.csv")
print(f"Fetched: {len(candles)} candles")

# Step 2 — clean
cleaner = DataCleaner()
clean_candles = cleaner.clean(candles)
print(f"After cleaning: {len(clean_candles)} candles")

# Step 3 — build feature matrix
builder = DatasetBuilder()
matrix = builder.build(clean_candles)
print(f"Feature matrix shape: {matrix.shape}")
print(f"First feature vector: {matrix[0]}")

# Step 4 — save
save_path = "data/features/eurusd_2020"
builder.save(matrix, save_path)
print(f"Saved to: {save_path}.npy")