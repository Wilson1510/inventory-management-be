# API Endpoints and Payload

## List
**Endpoint:** `GET /api/products/`

**Response:**
```json
[
    {
        "name": "Test Product 1",
        "sku_number": "TP-001",
        "category": {
            "id": 1,
            "name": "Test Category"
        },
        "base_price": 50000,
        "price": {
            "id": 1,
            "price": 55000,
            "minimum_quantity": 1,
            "unit": {
                "id": 1,
                "name": "pcs"
            }
        }, // base unit and minimum quantity 1
        "quantity": 4,
        "unit": {
            "id": 1,
            "name": "pcs"
        }, // base unit
        "id": 6,
        "created_at": "2026-04-04T06:22:34.514325Z",
        "created_by": 9,
        "updated_at": "2026-04-04T06:22:34.514327Z",
        "updated_by": null
    },
    {
        "name": "Test Product 2",
        "sku_number": "TP-002",
        "category": {
            "id": 1,
            "name": "Test Category"
        },
        "base_price": 51000,
        "price": {
            "id": 2,
            "price": 56000,
            "minimum_quantity": 1,
            "unit": {
                "id": 1,
                "name": "pcs"
            }
        },
        "quantity": 4,
        "unit": {
            "id": 1,
            "name": "pcs"
        },
        "id": 7,
        "created_at": "2026-04-04T07:22:34.514325Z",
        "created_by": 10,
        "updated_at": "2026-04-04T07:22:34.514327Z",
        "updated_by": 10
    }
]
```

## Retrieve
**Endpoint:** `GET /api/products/{id}`
**Response:**
```json
{
    "name": "Test Product",
    "sku_number": "TP-001",
    "category": {
        "id": 1,
        "name": "Test Category"
    },
    "base_price": 50000,
    "prices": [
        {
            "id": 1,
            "price": 55000,
            "minimum_quantity": 1,
            "unit": {
                "id": 1,
                "name": "pcs"
            }
        },
        {
            "id": 2,
            "price": 54000,
            "minimum_quantity": 3,
            "unit": {
                "id": 1,
                "name": "pcs"
            }
        },
        {
            "id": 3,
            "price": 530000,
            "minimum_quantity": 1,
            "unit": {
                "id": 2,
                "name": "pack"
            }
        },
        {
            "id": 4,
            "price": 3400000,
            "minimum_quantity": 1,
            "unit": {
                "id": 3,
                "name": "box"
            }
        }
    ],
    "quantity": 4,
    "units": [
        {
            "id": 1,
            "unit": {
                "id": 1,
                "name": "pcs"
            },
            "multiplier": 1,
            "is_base_unit": true
        },
        {
            "id": 2,
            "unit": {
                "id": 2,
                "name": "pack"
            },
            "multiplier": 10,
            "is_base_unit": false
        },
        {
            "id": 3,
            "unit": {
                "id": 3,
                "name": "box"
            },
            "multiplier": 60,
            "is_base_unit": false
        }
    ],
    "id": 6,
    "created_at": "2026-04-04T06:23:57.253807Z",
    "created_by": 9,
    "updated_at": "2026-04-04T06:23:57.253809Z",
    "updated_by": 9
}
```

## Create
**Endpoint:** `POST /api/products/`
**Request Body:**
```json
{
    "name": "Test Product",
    "category": 1,
    "prices": [
        {
            "price": 55000,
            "minimum_quantity": 1,
            "unit": 1
        },
        {
            "price": 54000,
            "minimum_quantity": 3,
            "unit": 1
        },
        {
            "price": 530000,
            "minimum_quantity": 1,
            "unit": 2
        },
        {
            "price": 3400000,
            "minimum_quantity": 1,
            "unit": 3
        }
    ],
    "units": [
        {
            "unit": 1,
            "multiplier": 1,
            "is_base_unit": true
        },
        {
            "unit": 2,
            "multiplier": 10,
            "is_base_unit": false
        },
        {
            "unit": 3,
            "multiplier": 60,
            "is_base_unit": false
        }
    ]
}
```
**Response:**
```json
{
    "name": "Test Product",
    "sku_number": "TP-001",
    "category": {
        "id": 1,
        "name": "Test Category"
    },
    "base_price": 0,
    "prices": [
        {
            "id": 1,
            "price": 55000,
            "minimum_quantity": 1,
            "unit": {
                "id": 1,
                "name": "pcs"
            }
        },
        {
            "id": 2,
            "price": 54000,
            "minimum_quantity": 3,
            "unit": {
                "id": 1,
                "name": "pcs"
            }
        },
        {
            "id": 3,
            "price": 530000,
            "minimum_quantity": 1,
            "unit": {
                "id": 2,
                "name": "pack"
            }
        },
        {
            "id": 4,
            "price": 3400000,
            "minimum_quantity": 1,
            "unit": {
                "id": 3,
                "name": "box"
            }
        }
    ],
    "quantity": 0,
    "units": [
        {
            "id": 1,
            "unit": {
                "id": 1,
                "name": "pcs"
            },
            "multiplier": 1,
            "is_base_unit": true
        },
        {
            "id": 2,
            "unit": {
                "id": 2,
                "name": "pack"
            },
            "multiplier": 10,
            "is_base_unit": false
        },
        {
            "id": 3,
            "unit": {
                "id": 3,
                "name": "box"
            },
            "multiplier": 60,
            "is_base_unit": false
        }
    ],
    "id": 6,
    "created_at": "2026-04-04T06:23:57.253807Z",
    "created_by": 9,
    "updated_at": "2026-04-04T06:23:57.253809Z",
    "updated_by": 9
}
```

## Update (PUT and PATCH)
**Endpoint:** `PUT /api/products/{id}`
**Request Body:**
PUT send all fields
PATCH send only changed fields
```json
{
    "name": "Test Update",
    "category": 2,
    "prices": [
        {
            "id": 1,
            "price": 56000,
            "minimum_quantity": 1,
            "unit": 1
        },
        {
            "id": 2,
            "price": 54000,
            "minimum_quantity": 3,
            "unit": 1
        },
        {
            "id": 3,
            "price": 530000,
            "minimum_quantity": 1,
            "unit": 2
        },
        {
            "id": 4,
            "price": 3400000,
            "minimum_quantity": 1,
            "unit": 3
        }
    ],
    "units": [
        {
            "id": 1,
            "unit": 1,
            "multiplier": 1,
            "is_base_unit": true
        },
        {
            "id": 2,
            "unit": 2,
            "multiplier": 10,
            "is_base_unit": false
        },
        {
            "id": 3,
            "unit": 3,
            "multiplier": 60,
            "is_base_unit": false
        }
    ]
}
```
**Response:**
PUT send all fields
PATCH send only changed fields
```json
{
    "name": "Test Product Update",
    "sku_number": "TP-001",
    "category": {
        "id": 2,
        "name": "Test Category"
    },
    "base_price": 0,
    "prices": [
        {
            "id": 1,
            "price": 56000,
            "minimum_quantity": 1,
            "unit": {
                "id": 1,
                "name": "pcs"
            }
        },
        {
            "id": 2,
            "price": 54000,
            "minimum_quantity": 3,
            "unit": {
                "id": 1,
                "name": "pcs"
            }
        },
        {
            "id": 3,
            "price": 530000,
            "minimum_quantity": 1,
            "unit": {
                "id": 2,
                "name": "pack"
            }
        },
        {
            "id": 4,
            "price": 3400000,
            "minimum_quantity": 1,
            "unit": {
                "id": 3,
                "name": "box"
            }
        }
    ],
    "quantity": 0,
    "units": [
        {
            "id": 1,
            "unit": {
                "id": 1,
                "name": "pcs"
            },
            "multiplier": 1,
            "is_base_unit": true
        },
        {
            "id": 2,
            "unit": {
                "id": 2,
                "name": "pack"
            },
            "multiplier": 10,
            "is_base_unit": false
        },
        {
            "id": 3,
            "unit": {
                "id": 3,
                "name": "box"
            },
            "multiplier": 60,
            "is_base_unit": false
        }
    ],
    "id": 6,
    "created_at": "2026-04-04T06:23:57.253807Z",
    "created_by": 9,
    "updated_at": "2026-04-04T06:23:57.253809Z",
    "updated_by": 9
}
```

## Delete
**Endpoint:** `DELETE /api/products/{id}`
**Response:** `204 No Content`