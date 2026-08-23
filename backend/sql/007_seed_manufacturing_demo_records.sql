-- 供本地演示和后续 Dashboard 联调用；可在执行 006 后单独执行。
INSERT INTO production_records (
    date, production_line, clinker_output, cement_output, planned_output,
    completion_rate, running_hours, downtime_hours
)
SELECT '2026-08-01', '1号线', 5000.00, 6500.00, 7000.00, 92.86, 22.50, 1.50
WHERE NOT EXISTS (
    SELECT 1 FROM production_records WHERE date = '2026-08-01' AND production_line = '1号线'
);

INSERT INTO equipment_records (
    date, equipment_name, status, running_hours, fault_count, temperature, vibration
)
SELECT '2026-08-01', '水泥磨', '运行', 22.50, 0, 65.00, 3.200
WHERE NOT EXISTS (
    SELECT 1 FROM equipment_records WHERE date = '2026-08-01' AND equipment_name = '水泥磨'
);

INSERT INTO energy_records (
    date, production_line, electricity_consumption, coal_consumption, unit_energy_consumption
)
SELECT '2026-08-01', '1号线', 75.00, 105.00, 98.50
WHERE NOT EXISTS (
    SELECT 1 FROM energy_records WHERE date = '2026-08-01' AND production_line = '1号线'
);
