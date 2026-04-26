# API Endpoints and Payload

* Customers mirrors suppliers, just change customers to suppliers and sales orders to purchase orders

## List
**Endpoint:** `GET /api/customers/`

**Response:**
```json
[
    {
        "name": "Test Customer",
        "business_entity": "PERORANGAN",
        "phone": "081234567890",
        "email": "test@customer.com",
        "address": "Jl. Test No. 123, Jakarta",
        "count_sales_orders": 10,
        "last_sales_order_date": "2026-04-04T06:22:34.514325Z",
        "total_sales_amount": "10000000.00",
        "id": 6,
        "created_at": "2026-04-04T06:22:34.514325Z",
        "created_by": 9,
        "updated_at": "2026-04-04T06:22:34.514327Z",
        "updated_by": null
    },
    {
        "name": "Test Customer 2",
        "business_entity": "PT",
        "phone": "081234567891",
        "email": "test2@customer.com",
        "address": "Jl. Test No. 124, Jakarta",
        "count_sales_orders": 10,
        "last_sales_order_date": "2026-04-04T06:22:34.514325Z",
        "total_sales_amount": "10000000.00",
        "id": 7,
        "created_at": "2026-04-04T07:22:34.514325Z",
        "created_by": 10,
        "updated_at": "2026-04-04T07:22:34.514327Z",
        "updated_by": 10
    }
]
```

## Retrieve
**Endpoint:** `GET /api/customers/{id}`
**Response:**
```json
{
    "name": "Test Customer",
    "business_entity": "PERORANGAN",
    "phone": "081234567890",
    "email": "test@customer.com",
    "address": "Jl. Test No. 123, Jakarta",
    "id": 6,
    "created_at": "2026-04-04T06:23:57.253807Z",
    "created_by": 9,
    "updated_at": "2026-04-04T06:23:57.253809Z",
    "updated_by": 9
}
```

## Create
**Endpoint:** `POST /api/customers/`
**Request Body:**
```json
{
    "name": "Test Customer",
    "business_entity": "PERORANGAN",
    "phone": "081234567890",
    "email": "test@customer.com",
    "address": "Jl. Test No. 123, Jakarta"
}
```
**Response:**
```json
{
    "name": "Test Customer",
    "business_entity": "PERORANGAN",
    "phone": "081234567890",
    "email": "test@customer.com",
    "address": "Jl. Test No. 123, Jakarta",
    "id": 6,
    "created_at": "2026-04-04T06:23:57.253807Z",
    "created_by": 9,
    "updated_at": "2026-04-04T06:23:57.253809Z",
    "updated_by": 9
}
```

## Update (PUT and PATCH)
**Endpoint:** `PUT /api/customers/{id}`
**Request Body:**
PUT send all fields
PATCH send only changed fields
```json
{
    "name": "Test Customer",
    "business_entity": "PERORANGAN",
    "phone": "081234567890",
    "email": "test@customer.com",
    "address": "Jl. Test No. 123, Jakarta"
}
```
**Response:**
PUT send all fields
PATCH send only changed fields
```json
{
    "name": "Test Customer",
    "business_entity": "PERORANGAN",
    "phone": "081234567890",
    "email": "test@customer.com",
    "address": "Jl. Test No. 123, Jakarta",
    "id": 6,
    "created_at": "2026-04-04T06:23:57.253807Z",
    "created_by": 9,
    "updated_at": "2026-04-04T06:23:57.253809Z",
    "updated_by": 9
}
```

## Delete
**Endpoint:** `DELETE /api/customers/{id}`
**Response:** `204 No Content`