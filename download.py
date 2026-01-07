import os
import zipfile
from huggingface_hub import snapshot_download

def download_and_extract_assets():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(root_dir, "assets")
    if os.path.exists(assets_dir) and os.listdir(assets_dir):
        print(f"Assets already exist at {assets_dir}, skipping download.")
        return assets_dir
    cache_dir = os.path.join(root_dir, ".hf_assets_cache")
    os.makedirs(cache_dir, exist_ok=True)
    snapshot_download(
        repo_id="flahm/MirrorBenchAssets",
        repo_type="dataset",
        local_dir=cache_dir,
        allow_patterns=["assets.zip"],
    )

    zip_path = os.path.join(cache_dir, "assets.zip")
    if not os.path.exists(zip_path):
        raise FileNotFoundError(f"Downloaded zip file not found at {zip_path}")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(root_dir)
    print(f"Assets downloaded and extracted to {assets_dir}")
    return assets_dir

if __name__ == "__main__":
    download_and_extract_assets()