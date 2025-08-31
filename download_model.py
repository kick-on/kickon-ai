from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="sentence-transformers/all-MiniLM-L6-v2",
    local_dir="all-MiniLM-L6-v2",
    local_dir_use_symlinks=False  # 실파일 저장 (심볼릭 링크 X)
)