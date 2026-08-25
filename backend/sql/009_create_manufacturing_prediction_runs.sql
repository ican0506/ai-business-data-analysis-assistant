CREATE TABLE IF NOT EXISTS manufacturing_prediction_runs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    prediction_type VARCHAR(50) NOT NULL,
    scope_type VARCHAR(50) NOT NULL,
    scope_name VARCHAR(100) NULL,
    period_start DATE NULL,
    period_end DATE NULL,
    forecast_horizon_days INT NOT NULL,
    algorithm_version VARCHAR(50) NOT NULL,
    risk_level VARCHAR(20) NULL,
    data_snapshot JSON NOT NULL,
    prediction_result JSON NOT NULL,
    ai_mode VARCHAR(30) NOT NULL,
    ai_summary TEXT NOT NULL,
    generated_at DATETIME NOT NULL,
    created_at DATETIME NOT NULL,
    CONSTRAINT fk_manufacturing_prediction_runs_user
        FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_manufacturing_prediction_runs_user_generated (user_id, generated_at),
    INDEX idx_manufacturing_prediction_runs_scope_generated
        (prediction_type, scope_type, scope_name, generated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
