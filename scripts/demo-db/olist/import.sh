#!/usr/bin/env bash
set -Eeuo pipefail

# Olist CSV import for AskMyData public demo.
# Run from the AskMyData project root.

CONTAINER="${OLIST_CONTAINER:-askmydata-demo-db-test}"
DATABASE="${OLIST_DATABASE:-olist_schema_test}"
CSV_DIR="backups/demo-db/olist/raw"

import_csv() {
    local table="$1"
    local filename="$2"
    local columns="$3"

    echo "Importing ${table}..."

    docker exec -i "$CONTAINER" \
        psql -X -v ON_ERROR_STOP=1 \
        -U postgres -d "$DATABASE" \
        -c "COPY ${table} (${columns}) FROM STDIN WITH (FORMAT csv, HEADER true, NULL '');" \
        < "${CSV_DIR}/${filename}"
}

import_csv customers \
    olist_customers_dataset.csv \
    "customer_id, customer_unique_id, customer_zip_code_prefix, customer_city, customer_state"

import_csv sellers \
    olist_sellers_dataset.csv \
    "seller_id, seller_zip_code_prefix, seller_city, seller_state"

import_csv product_category_name_translation \
    product_category_name_translation.csv \
    "product_category_name, product_category_name_english"

import_csv products \
    olist_products_dataset.csv \
    "product_id, product_category_name, product_name_lenght, product_description_lenght, product_photos_qty, product_weight_g, product_length_cm, product_height_cm, product_width_cm"

import_csv orders \
    olist_orders_dataset.csv \
    "order_id, customer_id, order_status, order_purchase_timestamp, order_approved_at, order_delivered_carrier_date, order_delivered_customer_date, order_estimated_delivery_date"

import_csv order_items \
    olist_order_items_dataset.csv \
    "order_id, order_item_id, product_id, seller_id, shipping_limit_date, price, freight_value"

import_csv order_payments \
    olist_order_payments_dataset.csv \
    "order_id, payment_sequential, payment_type, payment_installments, payment_value"

import_csv order_reviews \
    olist_order_reviews_dataset.csv \
    "review_id, order_id, review_score, review_comment_title, review_comment_message, review_creation_date, review_answer_timestamp"

import_csv geolocation \
    olist_geolocation_dataset.csv \
    "geolocation_zip_code_prefix, geolocation_lat, geolocation_lng, geolocation_city, geolocation_state"

echo "Olist import completed."