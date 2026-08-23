CREATE TABLE IF NOT EXISTS production_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    production_line VARCHAR(100) NOT NULL,
    clinker_output DECIMAL(12, 2) NOT NULL,
    cement_output DECIMAL(12, 2) NOT NULL,
    planned_output DECIMAL(12, 2) NOT NULL,
    completion_rate DECIMAL(7, 2) NOT NULL,
    running_hours DECIMAL(7, 2) NOT NULL,
    downtime_hours DECIMAL(7, 2) NOT NULL,
    INDEX idx_production_records_date (date),
    INDEX idx_production_records_line (production_line)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS equipment_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    equipment_name VARCHAR(100) NOT NULL,
    status VARCHAR(30) NOT NULL,
    running_hours DECIMAL(7, 2) NOT NULL,
    fault_count INT NOT NULL DEFAULT 0,
    temperature DECIMAL(7, 2) NOT NULL,
    vibration DECIMAL(7, 3) NOT NULL,
    INDEX idx_equipment_records_date (date),
    INDEX idx_equipment_records_name (equipment_name),
    INDEX idx_equipment_records_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS energy_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    production_line VARCHAR(100) NOT NULL,
    electricity_consumption DECIMAL(12, 2) NOT NULL,
    coal_consumption DECIMAL(12, 2) NOT NULL,
    unit_energy_consumption DECIMAL(12, 2) NOT NULL,
    INDEX idx_energy_records_date (date),
    INDEX idx_energy_records_line (production_line)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
