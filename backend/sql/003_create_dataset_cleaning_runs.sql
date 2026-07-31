CREATE TABLE IF NOT EXISTS dataset_cleaning_runs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dataset_id INT NOT NULL,
    cleaned_storage_path VARCHAR(500) NOT NULL,
    original_row_count INT NOT NULL,
    cleaned_row_count INT NOT NULL,
    removed_empty_rows INT NOT NULL DEFAULT 0,
    removed_duplicate_rows INT NOT NULL DEFAULT 0,
    invalid_value_count INT NOT NULL DEFAULT 0,
    missing_value_count INT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL,
    CONSTRAINT uk_dataset_cleaning_runs_storage_path UNIQUE (cleaned_storage_path),
    CONSTRAINT fk_dataset_cleaning_runs_dataset FOREIGN KEY (dataset_id) REFERENCES datasets(id),
    INDEX idx_dataset_cleaning_runs_dataset_id (dataset_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
