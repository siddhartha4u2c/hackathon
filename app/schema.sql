CREATE TABLE IF NOT EXISTS dealers (
    dealer_id TEXT PRIMARY KEY, dealer_name TEXT, region TEXT, country TEXT,
    city TEXT, tier TEXT, status TEXT, contact_email TEXT,
    credit_limit_eur NUMERIC, onboarded_date DATE
);
CREATE TABLE IF NOT EXISTS parts (
    part_no TEXT PRIMARY KEY, description TEXT, category TEXT, unit_price_eur NUMERIC,
    warranty_months INTEGER, supplier TEXT, status TEXT
);
CREATE TABLE IF NOT EXISTS purchase_orders (
    po_no TEXT NOT NULL, po_line_no INTEGER NOT NULL, dealer_id TEXT, part_no TEXT,
    order_qty INTEGER, unit_price_eur NUMERIC, line_total_eur NUMERIC,
    order_date DATE, requested_delivery_date DATE, po_status TEXT,
    shipment_id TEXT, currency TEXT, PRIMARY KEY (po_no, po_line_no)
);
CREATE TABLE IF NOT EXISTS shipments (
    shipment_id TEXT PRIMARY KEY, po_no TEXT, dealer_id TEXT, carrier TEXT,
    ship_date DATE, est_delivery_date DATE, actual_delivery_date DATE,
    shipment_status TEXT, tracking_no TEXT, qty INTEGER
);
CREATE TABLE IF NOT EXISTS claims (
    claim_id TEXT PRIMARY KEY, claim_type TEXT, dealer_id TEXT, part_no TEXT,
    po_no TEXT, claim_qty INTEGER, purchase_date DATE, claim_date DATE,
    claim_status TEXT, reason TEXT, claim_amount_eur NUMERIC, resolution_code TEXT
);
CREATE TABLE IF NOT EXISTS inventory (
    inventory_id TEXT PRIMARY KEY, part_no TEXT, warehouse_loc TEXT,
    on_hand_qty INTEGER, reserved_qty INTEGER, available_qty INTEGER,
    reorder_point INTEGER, bin_location TEXT, last_count_date DATE
);
CREATE TABLE IF NOT EXISTS bom (
    bom_id TEXT PRIMARY KEY, assembly_part_no TEXT, component_part_no TEXT,
    qty_per INTEGER, level INTEGER, notes TEXT
);
CREATE TABLE IF NOT EXISTS knowledge (
    doc_id TEXT PRIMARY KEY, doc_type TEXT, title TEXT, module TEXT,
    error_code TEXT, summary TEXT, last_updated DATE, owner_team TEXT
);
CREATE TABLE IF NOT EXISTS data_quality_findings (
    finding_id BIGSERIAL PRIMARY KEY, entity_type TEXT NOT NULL, entity_id TEXT NOT NULL,
    scenario_code TEXT NOT NULL, severity TEXT NOT NULL, message TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(), UNIQUE(entity_type, entity_id, scenario_code)
);
