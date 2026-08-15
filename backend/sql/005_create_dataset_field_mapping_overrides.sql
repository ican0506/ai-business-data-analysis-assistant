CREATE TABLE IF NOT EXISTS dataset_field_mapping_overrides (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dataset_id INT NOT NULL,
    source_column VARCHAR(255) NOT NULL,
    target_field VARCHAR(100) NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    CONSTRAINT uk_dataset_mapping_override_source UNIQUE (dataset_id, source_column),
    CONSTRAINT uk_dataset_mapping_override_target UNIQUE (dataset_id, target_field),
    CONSTRAINT fk_dataset_mapping_override_dataset
        FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE,
    INDEX idx_dataset_mapping_override_dataset_id (dataset_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
