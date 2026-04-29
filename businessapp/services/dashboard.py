from datetime import timedelta
from decimal import Decimal
from django.db.models import (
    Case, DecimalField, ExpressionWrapper, F, IntegerField, OuterRef, Subquery, Sum, Value, When
)
from django.db.models.functions import Coalesce
from django.utils import timezone

from businessapp.models import (
    Customer, Delivery, DeliveryItem, Product, ProductUnit, PurchaseOrder, Receipt, SalesOrder,
    SalesOrderItem
)

DASHBOARD_PERIOD_DAYS = 30
TOP_WIDGET_LIMIT = 5


def _period_start():
    return timezone.now() - timedelta(days=DASHBOARD_PERIOD_DAYS)


def _sales_order_line_price_subquery():
    return Subquery(
        SalesOrderItem.objects.filter(
            sales_id=OuterRef("delivery__sales_order_id"),
            product_id=OuterRef("product_id"),
            unit_id=OuterRef("unit_id"),
        ).values("price")[:1],
        output_field=DecimalField(max_digits=10, decimal_places=2),
    )


def _product_unit_multiplier_subquery():
    return Subquery(
        ProductUnit.objects.filter(
            product_id=OuterRef("product_id"),
            unit_id=OuterRef("unit_id"),
        ).values("multiplier")[:1],
        output_field=IntegerField(),
    )


def _fulfilled_delivery_items_in_period():
    return DeliveryItem.objects.filter(
        delivery__status=Delivery.Status.DONE,
        delivery__checked_at__gte=_period_start(),
        quantity_delivered__gt=0,
    ).annotate(
        so_price=_sales_order_line_price_subquery(),
        mult=Coalesce(_product_unit_multiplier_subquery(), Value(1)),
    )


def total_revenue_last_30_days():
    qs = _fulfilled_delivery_items_in_period().annotate(
        line_revenue=ExpressionWrapper(
            F("quantity_delivered") * F("so_price"),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )
    )
    total = qs.aggregate(
        t=Coalesce(
            Sum("line_revenue"),
            Value(0),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )
    )["t"]
    return total


def gross_margin_last_30_days():
    qs = _fulfilled_delivery_items_in_period().annotate(
        line_revenue=ExpressionWrapper(
            F("quantity_delivered") * F("so_price"),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        ),
        line_cogs=Case(
            When(
                base_unit_cost_snapshot__isnull=False,
                then=ExpressionWrapper(
                    F("quantity_delivered")
                    * F("mult")
                    * F("base_unit_cost_snapshot"),
                    output_field=DecimalField(max_digits=14, decimal_places=2),
                ),
            ),
            default=Value(Decimal("0")),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        ),
    )
    agg = qs.aggregate(
        rev=Coalesce(
            Sum("line_revenue"),
            Value(0),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        ),
        cogs=Coalesce(
            Sum("line_cogs"),
            Value(0),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        ),
    )
    return agg["rev"] - agg["cogs"]


def active_sales_orders_count():
    return (
        SalesOrder.objects.filter(
            status=SalesOrder.Status.CONFIRMED,
            deliveries__status=Delivery.Status.DRAFT,
        ).distinct().count()
    )


def active_purchase_orders_count():
    return (
        PurchaseOrder.objects.filter(
            status=PurchaseOrder.Status.CONFIRMED,
            receipts__status=Receipt.Status.DRAFT,
        ).distinct().count()
    )


def top_selling_products(limit=TOP_WIDGET_LIMIT):
    rows = (
        _fulfilled_delivery_items_in_period()
        .annotate(
            base_qty=ExpressionWrapper(
                F("quantity_delivered") * F("mult"),
                output_field=IntegerField(),
            )
        )
        .values("product_id")
        .annotate(sold_qty=Sum("base_qty"))
        .order_by("-sold_qty")[:limit]
    )
    product_ids = [r["product_id"] for r in rows]
    products = {p.id: p for p in Product.objects.filter(id__in=product_ids)}

    product_units = ProductUnit.objects.filter(
        product_id__in=product_ids, is_base_unit=True
    ).select_related("unit")
    base_units = {pu.product_id: pu.unit.name for pu in product_units}

    out = []
    for r in rows:
        p = products.get(r["product_id"])
        if p:
            out.append(
                {
                    "id": p.id,
                    "sku_number": p.sku_number,
                    "name": p.name,
                    "sold_qty": r["sold_qty"] or 0,
                    "unit": base_units.get(p.id, ""),
                }
            )
    return out


def slow_moving_products(limit=TOP_WIDGET_LIMIT):
    rows = (
        _fulfilled_delivery_items_in_period()
        .annotate(
            base_qty=ExpressionWrapper(
                F("quantity_delivered") * F("mult"),
                output_field=IntegerField(),
            )
        )
        .values("product_id")
        .annotate(sold_qty=Sum("base_qty"))
        .order_by("sold_qty")[:limit]
    )
    product_ids = [r["product_id"] for r in rows]
    products = {p.id: p for p in Product.objects.filter(id__in=product_ids)}

    product_units = ProductUnit.objects.filter(
        product_id__in=product_ids, is_base_unit=True
    ).select_related("unit")
    base_units = {pu.product_id: pu.unit.name for pu in product_units}

    out = []
    for r in rows:
        p = products.get(r["product_id"])
        if p:
            out.append(
                {
                    "id": p.id,
                    "sku_number": p.sku_number,
                    "name": p.name,
                    "sold_qty": r["sold_qty"] or 0,
                    "unit": base_units.get(p.id, ""),
                }
            )
    return out


def top_customers_by_recognized_revenue(limit=TOP_WIDGET_LIMIT):
    rows = (
        _fulfilled_delivery_items_in_period()
        .annotate(
            line_revenue=ExpressionWrapper(
                F("quantity_delivered") * F("so_price"),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )
        )
        .values("delivery__sales_order__customer_id")
        .annotate(
            total_purchased=Coalesce(
                Sum("line_revenue"),
                Value(0),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )
        )
        .order_by("-total_purchased")[:limit]
    )
    customer_ids = [r["delivery__sales_order__customer_id"] for r in rows]
    customers = {c.id: c for c in Customer.objects.filter(id__in=customer_ids)}
    out = []
    for r in rows:
        cid = r["delivery__sales_order__customer_id"]
        c = customers.get(cid)
        if c:
            out.append(
                {
                    "id": c.id,
                    "name": c.name,
                    "total_purchased": r["total_purchased"] or Decimal("0"),
                }
            )
    return out


def metrics_payload():
    return {
        "total_revenue": total_revenue_last_30_days(),
        "gross_margin": gross_margin_last_30_days(),
        "active_sales_orders": active_sales_orders_count(),
        "active_purchase_orders": active_purchase_orders_count(),
    }


def top_data_payload():
    return {
        "top_selling_products": top_selling_products(),
        "slow_moving_products": slow_moving_products(),
        "top_customers": top_customers_by_recognized_revenue(),
    }
