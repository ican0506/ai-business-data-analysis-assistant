CREATE TABLE IF NOT EXISTS manufacturing_business_reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    period_start DATE NULL,
    period_end DATE NULL,
    risk_level VARCHAR(20) NOT NULL,
    ai_mode VARCHAR(30) NOT NULL,
    summary TEXT NOT NULL,
    snapshot JSON NOT NULL,
    generated_at DATETIME NOT NULL,
    created_at DATETIME NOT NULL,
    CONSTRAINT fk_manufacturing_business_reports_user
        FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_manufacturing_business_reports_generated_at (generated_at),
    INDEX idx_manufacturing_business_reports_user_generated (user_id, generated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
