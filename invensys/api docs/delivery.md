# API Endpoints and Payload

* Receipt mirrors Delivery, mapped to purchase_order_id and arrival_date

## List
**Endpoint:** `GET /api/deliveries/`

**Response:**
```json
[
    {
        "number": "DLV-00001",
        "status": "DRAFT",
        "method": "DELIVERY",
        "sales_order": { "id": 1, "number": "SO-00001" },
        "delivery_date": "2026-05-15",
        "id": 6,
        "created_at": "2026-04-04T06:22:34.514325Z",
        "created_by": 9,
        "updated_at": "2026-04-04T06:22:34.514327Z",
        "updated_by": null
    },
    {
        "number": "DLV-00002",
        "status": "DONE",
        "method": "PICKUP",
        "sales_order": { "id": 2, "number": "SO-00002" },
        "delivery_date": "2026-05-15",
        "id": 7,
        "created_at": "2026-04-04T07:22:34.514325Z",
        "created_by": 10,
        "updated_at": "2026-04-04T07:22:34.514327Z",
        "updated_by": 10
    }
]
```

## Retrieve
**Endpoint:** `GET /api/deliveries/{id}`
**Response:**
```json
{
    "number": "DLV-00001",
    "status": "DRAFT",
    "method": "DELIVERY",
    "sales_order": { "id": 1, "number": "SO-00001" },
    "delivery_date": "2026-05-15",
    "notes": "Urgent shipment",
    "checked_by": null,
    "checked_at": null,
    "destination": "123 Business Rd, City",
    "items": [
        {
            "id": 1,
            "product": { "id": 1, "name": "Mouse" },
            "quantity": 10,
            "quantity_delivered": 0,
            "unit": { "id": 1, "name": "Piece" },
            "notes": "Urgent shipment"
        },
        {
            "id": 2,
            "product": { "id": 2, "name": "Keyboard" },
            "quantity": 20,
            "quantity_delivered": 0,
            "unit": { "id": 2, "name": "Piece" },
            "notes": "Urgent shipment"
        }
    ],
    "id": 6,
    "created_at": "2026-04-04T06:23:57.253807Z",
    "created_by": 9,
    "updated_at": "2026-04-04T06:23:57.253809Z",
    "updated_by": 9
}
```

## Update (PATCH)
**Endpoint:** `PATCH /api/deliveries/{id}`
**Request Body:**
```json
{
    "notes": "Handle with care",
    "method": "PICKUP",
    "items": [
        {
            "id": 1,
            "quantity_delivered": 10,
            "notes": "All accounted for"
        },
        {
            "id": 2,
            "quantity_delivered": 20,
            "notes": "All accounted for"
        }
    ]
}
```
**Response:**
```json
{
    "number": "DLV-00001",
    "status": "DRAFT",
    "method": "PICKUP",
    "sales_order": { "id": 1, "number": "SO-00001" },
    "delivery_date": "2026-05-15",
    "notes": "Handle with care",
    "checked_by": null,
    "checked_at": null,
    "destination": "123 Business Rd, City",
    "items": [
        {
            "id": 1,
            "product": { "id": 1, "name": "Mouse" },
            "quantity": 10,
            "quantity_delivered": 0,
            "unit": { "id": 1, "name": "Piece" },
            "notes": "All accounted for"
        },
        {
            "id": 2,
            "product": { "id": 2, "name": "Keyboard" },
            "quantity": 20,
            "quantity_delivered": 0,
            "unit": { "id": 2, "name": "Piece" },
            "notes": "All accounted for"
        }
    ],
    "id": 6,
    "created_at": "2026-04-04T06:23:57.253807Z",
    "created_by": 9,
    "updated_at": "2026-04-04T06:23:57.253809Z",
    "updated_by": 9
}
```

## Done
**Endpoint:** `POST /api/deliveries/{id}/done/`
**Response:** `200 OK`

## Cancel
**Endpoint:** `POST /api/deliveries/{id}/cancel/`
**Response:** `200 OK`