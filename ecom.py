import sqlite3
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

DB_PATH = "ecommerce_portfolio.db"
OUT_DIR = Path("outputs")
CHART_DIR = OUT_DIR / "charts"

OUT_DIR.mkdir(exist_ok=True)
CHART_DIR.mkdir(parents=True, exist_ok=True)
def run_sql(querry: str, params:tuple = ()) -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(querry, conn, params=params)


##таблицы в бд
tables = run_sql("SELECT name FROM sqlite_master WHERE type='table';")
print("table DB: \n", tables)

##метрики
unique_customer= run_sql("""
SELECT COUNT(DISTINCT customer_id) AS unique_customer
FROM orders;
""")


total_revenue  = run_sql("""
SELECT SUM(total_amount) AS total_revenue
FROM orders;
""")

avg_order_value = run_sql("""
SELECT AVG(total_amount) AS avg_order_value
FROM orders;
""")

order_count = run_sql("""
SELECT COUNT(*) AS total_oreders
FROM orders;
""")

print("\n===метрики===")
print(unique_customer)
print(total_revenue)
print(avg_order_value)
print(order_count)


#csv otch
pd.concat([unique_customer, total_revenue, avg_order_value, order_count], axis=1)\
  .to_csv(OUT_DIR / "kpis.csv", index=False)


#Выручка категория
by_category = run_sql("""
SELECT
    p.category,
    SUM(oi.quantity * p.price) AS revenue
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
GROUP BY p.category
ORDER BY revenue DESC;
""")

by_category.to_csv(OUT_DIR / "revenue_by_category.csv", index=False)
print("\nВыручка по категориям:\n", by_category)

#визуализация bar chart
plt.figure()
plt.bar(by_category["category"], by_category["revenue"])
plt.title("Revenue by Category")
plt.xlabel("Category")
plt.ylabel("Revenue")
plt.xticks(rotation=20)
plt.tight_layout()
plt.savefig(CHART_DIR / "revenue_by_category.png", dpi=150)
plt.close()

#новые/повторные заказы
new_vs_repeat = run_sql("""
WITH first_order AS (
    SELECT customer_id, MIN(order_date) AS first_purchase_date
    FROM orders
    GROUP BY customer_id
)
SELECT
    SUM(CASE WHEN o.order_date = f.first_purchase_date THEN 1 ELSE 0 END) AS first_time_orders,
    SUM(CASE WHEN o.order_date > f.first_purchase_date THEN 1 ELSE 0 END) AS repeat_orders
FROM orders o
JOIN first_order f ON o.customer_id = f.customer_id;
""")

new_vs_repeat.to_csv(OUT_DIR / "new_vs_repeat.csv", index=False)
print("\nНовые vs повторные заказы:\n", new_vs_repeat)

plt.figure()
plt.bar(["orders"], new_vs_repeat["first_time_orders"], label="First-time")
plt.bar(["orders"], new_vs_repeat["repeat_orders"], bottom=new_vs_repeat["first_time_orders"], label="Repeat")
plt.title("First-time vs Repeat Orders")
plt.ylabel("Orders")
plt.legend()
plt.tight_layout()
plt.savefig(CHART_DIR / "first_vs_repeat.png", dpi=150)
plt.close()

by_month = run_sql("""
SELECT 
    strftime('%Y-%m', order_date) AS month,
    COUNT(*) AS orders,
    SUM(total_amount) AS revenue,
    ROUND(AVG(total_amount), 2) AS avg_order_value
FROM orders
GROUP BY month
ORDER BY month;
""")
by_month.to_csv(OUT_DIR / "by_month.csv", index=False)
print("\nДинамика по месяцам:\n", by_month)

# Линейный график: заказы
plt.figure()
plt.plot(by_month["month"], by_month["orders"], marker="o")
plt.title("Orders by Month")
plt.xlabel("Month")
plt.ylabel("Orders")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig(CHART_DIR / "orders_by_month.png", dpi=150)
plt.close()

# Линейный график: выручка
plt.figure()
plt.plot(by_month["month"], by_month["revenue"], marker="o")
plt.title("Revenue by Month")
plt.xlabel("Month")
plt.ylabel("Revenue")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig(CHART_DIR / "revenue_by_month.png", dpi=150)
plt.close()

#топ 10 
top_products = run_sql("""
SELECT 
    p.product_name,
    p.category,
    SUM(oi.quantity) AS qty,
    ROUND(SUM(oi.quantity * p.price), 2) AS revenue
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
GROUP BY p.product_id, p.product_name, p.category
ORDER BY revenue DESC
LIMIT 10;
""")
top_products.to_csv(OUT_DIR / "top_products.csv", index=False)
print("\nTop-10 продуктов:\n", top_products)

print("\nГотово! Файлы сохранены в папке:", OUT_DIR.resolve())