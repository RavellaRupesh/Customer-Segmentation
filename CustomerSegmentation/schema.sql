CREATE DATABASE IF NOT EXISTS CustomerSegmentationDB;
USE CustomerSegmentationDB;

CREATE TABLE IF NOT EXISTS customers (
    customer_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_code VARCHAR(20) NOT NULL UNIQUE,
    signup_date DATE NULL
);

CREATE TABLE IF NOT EXISTS orders (
    order_id INT PRIMARY KEY,
    customer_id INT NOT NULL,
    order_date DATE NOT NULL,
    order_status VARCHAR(20) NOT NULL,
    CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS order_items (
    item_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    CONSTRAINT fk_items_order FOREIGN KEY (order_id)
        REFERENCES orders(order_id),
    CONSTRAINT chk_quantity CHECK (quantity > 0),
    CONSTRAINT chk_unit_price CHECK (unit_price >= 0)
);

CREATE TABLE IF NOT EXISTS segment_runs (
    run_id INT PRIMARY KEY AUTO_INCREMENT,
    method VARCHAR(30) NOT NULL,
    run_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    parameters JSON NULL
);

CREATE TABLE IF NOT EXISTS customer_segments (
    run_id INT NOT NULL,
    customer_id INT NOT NULL,
    segment_label VARCHAR(100) NOT NULL,
    PRIMARY KEY (run_id, customer_id),
    CONSTRAINT fk_segments_run FOREIGN KEY (run_id)
        REFERENCES segment_runs(run_id),
    CONSTRAINT fk_segments_customer FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)
);
