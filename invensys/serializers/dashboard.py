from rest_framework import serializers


class DashboardMetricsSerializer(serializers.Serializer):
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    gross_margin = serializers.DecimalField(max_digits=12, decimal_places=2)
    active_sales_orders = serializers.IntegerField()
    active_purchase_orders = serializers.IntegerField()


class TopProductWidgetSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    sku_number = serializers.CharField()
    name = serializers.CharField()
    sold_qty = serializers.IntegerField()


class TopCustomerWidgetSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    total_purchased = serializers.DecimalField(max_digits=14, decimal_places=2)


class DashboardTopDataSerializer(serializers.Serializer):
    top_selling_products = TopProductWidgetSerializer(many=True)
    slow_moving_products = TopProductWidgetSerializer(many=True)
    top_customers = TopCustomerWidgetSerializer(many=True)
