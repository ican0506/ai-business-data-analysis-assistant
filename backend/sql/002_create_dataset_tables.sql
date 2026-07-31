CREATE TABLE IF NOT EXISTS datasets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    owner_id INT NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    storage_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(10) NOT NULL,
    file_size INT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'UPLOADED',
    row_count INT NOT NULL DEFAULT 0,
    column_count INT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL,
    CONSTRAINT uk_datasets_storage_path UNIQUE (storage_path),
    CONSTRAINT fk_datasets_owner FOREIGN KEY (owner_id) REFERENCES users(id),
    INDEX idx_datasets_owner_id (owner_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS dataset_columns (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dataset_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    data_type VARCHAR(30) NOT NULL,
    position INT NOT NULL,
    missing_count INT NOT NULL DEFAULT 0,
    unique_count INT NOT NULL DEFAULT 0,
    CONSTRAINT fk_dataset_columns_dataset FOREIGN KEY (dataset_id) REFERENCES datasets(id),
    INDEX idx_dataset_columns_dataset_id (dataset_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
