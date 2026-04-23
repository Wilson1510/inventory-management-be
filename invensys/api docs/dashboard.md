# API Endpoints and Payload

## Metrics
**Endpoint:** `GET /api/dashboard/metrics/`

**Response:**
```json
{
    "total_revenue": "45000.00",
    "gross_margin": "12500.00",
    "active_sales_orders": 8,
    "active_purchase_orders": 3
}
```

## Top Data Widgets
**Endpoint:** `GET /api/dashboard/top-data/`

**Response:**
```json
{
    "top_selling_products": [
        {
            "id": 1,
            "sku_number": "SKU-XXX",
            "name": "Premium Widget",
            "sold_qty": 350,
            "unit": "Pcs"
        },
        {
            "id": 2,
            "sku_number": "SKU-YYY",
            "name": "Premium Widget 2",
            "sold_qty": 250,
            "unit": "Pcs"
        }
    ],
    "slow_moving_products": [
        {
            "id": 3,
            "sku_number": "SKU-ZZZ",
            "name": "Premium Widget 3",
            "sold_qty": 150,
            "unit": "Set"
        },
        {
            "id": 4,
            "sku_number": "SKU-AAA",
            "name": "Premium Widget 4",
            "sold_qty": 100,
            "unit": "Pcs"
        }
    ],
    "top_customers": [
        {
            "id": 5,
            "name": "ACME Corp",
            "total_purchased": "15000.00"
        },
        {
            "id": 6,
            "name": "ACME Corp 2",
            "total_purchased": "10000.00"
        }
    ]
}