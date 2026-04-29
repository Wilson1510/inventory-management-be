# Inventory Management Backend

A comprehensive, robust Business Management System backend API built with Django and Django REST Framework. This application serves as a lightweight ERP, managing the entire lifecycle of products, inventory, customers, suppliers, and order fulfillment.

## Features

* **Authentication & Authorization:** Secure JWT-based authentication using `djangorestframework-simplejwt`. Custom user models with role-based access.
* **Catalog Management:** 
  * Products with dynamic pricing tiers and multiple unit conversions.
  * Categories and Units management.
* **Contact Management:** Maintain profiles for Customers and Suppliers.
* **Order Management:** 
  * **Sales Orders:** Track customer orders, status, and fulfillment.
  * **Purchase Orders:** Manage supplier orders and stock replenishment.
* **Shipment & Logistics:**
  * **Deliveries:** Outbound stock tracking linked to Sales Orders.
  * **Receipts:** Inbound stock tracking linked to Purchase Orders.
* **Dashboard Analytics:** Aggregated data for high-level business overview.
* **Error Handling:** Centralized custom exception handler for consistent and standardized API error responses.

## Tech Stack

* **Framework:** Python 3, Django 5.2, Django REST Framework 3.17
* **Database:** PostgreSQL (`psycopg2-binary`)
* **Authentication:** JWT (`djangorestframework-simplejwt`)
* **Deployment & Production:**
  * WSGI server: Gunicorn
  * Static file serving: Whitenoise
* **Testing:** Pytest / Django Test Framework with `coverage`.

## Prerequisites

* Python 3.10+
* PostgreSQL database

## Local Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd inventory-management-be
   ```

2. **Set up a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Create a `.env` file in the root directory. You can use `.env.example` as a template:
   ```env
   SECRET_KEY=your-secret-key
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   ENV=dev

   # Database Settings
   DB_NAME=your_db_name
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_HOST=localhost
   DB_PORT=5432
   
   # JWT Configuration (optional)
   ACCESS_TOKEN_LIFETIME=15
   REFRESH_TOKEN_LIFETIME=7
   ```

5. **Run Migrations:**
   ```bash
   python manage.py migrate
   ```

6. **Run the server:**
   ```bash
   python manage.py runserver
   ```

## API Structure

The main entry point for the APIs is under `/api/` (configurable in main urls). Core endpoints include:

* `POST /auth/login/` - Obtain JWT token
* `POST /auth/refresh/` - Refresh JWT token
* `/users/` - User management
* `/categories/` - Product categories
* `/units/` - Measurement units
* `/products/` - Products catalog
* `/customers/` - Customer management
* `/suppliers/` - Supplier management
* `/sales-orders/` - Sales orders
* `/purchase-orders/` - Purchase orders
* `/deliveries/` - Outbound deliveries
* `/receipts/` - Inbound receipts
* `/dashboard/` - Analytical dashboard metrics

## Running Tests

To run tests and check code coverage:
```bash
coverage run manage.py test
coverage report
```
