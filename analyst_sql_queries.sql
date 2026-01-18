-- ============================================================================
-- DATA ANALYST: ESSENTIAL SQL QUERIES
-- ============================================================================

-- ============================================================================
-- 1. BASIC DATA EXPLORATION QUERIES
-- ============================================================================

-- Count total records
SELECT COUNT(*) as total_records FROM sales_transactions;

-- Get data types and column info
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'sales_transactions';

-- Check for duplicates
SELECT 
    order_id, 
    COUNT(*) as occurrence_count
FROM sales_transactions
GROUP BY order_id
HAVING COUNT(*) > 1;

-- Check for null values
SELECT 
    SUM(CASE WHEN order_id IS NULL THEN 1 ELSE 0 END) as null_order_id,
    SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) as null_customer_id,
    SUM(CASE WHEN price IS NULL THEN 1 ELSE 0 END) as null_price
FROM sales_transactions;

-- ============================================================================
-- 2. SALES TRENDS ANALYSIS
-- ============================================================================

-- Monthly sales trend
SELECT 
    DATE_TRUNC('month', order_date)::DATE as month,
    COUNT(*) as order_count,
    COUNT(DISTINCT customer_id) as unique_customers,
    SUM(price) as total_revenue,
    AVG(price) as avg_order_value,
    MIN(price) as min_price,
    MAX(price) as max_price
FROM sales_transactions
GROUP BY DATE_TRUNC('month', order_date)
ORDER BY month DESC;

-- Daily sales with 7-day moving average
WITH daily_sales AS (
    SELECT 
        DATE(order_date) as sale_date,
        COUNT(*) as daily_orders,
        SUM(price) as daily_revenue
    FROM sales_transactions
    GROUP BY DATE(order_date)
)
SELECT 
    sale_date,
    daily_orders,
    daily_revenue,
    ROUND(
        AVG(daily_revenue) OVER (
            ORDER BY sale_date 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ), 2
    ) as moving_avg_7day
FROM daily_sales
ORDER BY sale_date DESC;

-- ============================================================================
-- 3. PRODUCT ANALYSIS
-- ============================================================================

-- Top 20 products by revenue
SELECT 
    product_id,
    product_category,
    COUNT(*) as order_count,
    COUNT(DISTINCT customer_id) as unique_customers,
    SUM(price) as total_revenue,
    AVG(price) as avg_price,
    MIN(price) as min_price,
    MAX(price) as max_price,
    ROUND(
        (SUM(price) / SUM(SUM(price)) OVER ()) * 100, 2
    ) as revenue_percentage
FROM sales_transactions
GROUP BY product_id, product_category
ORDER BY total_revenue DESC
LIMIT 20;

-- Revenue concentration (Pareto analysis)
WITH product_revenue AS (
    SELECT 
        product_id,
        SUM(price) as revenue,
        ROW_NUMBER() OVER (ORDER BY SUM(price) DESC) as rank
    FROM sales_transactions
    GROUP BY product_id
),
revenue_percentile AS (
    SELECT 
        *,
        SUM(revenue) OVER (ORDER BY rank) as cumulative_revenue,
        SUM(revenue) OVER () as total_revenue
    FROM product_revenue
)
SELECT 
    rank,
    product_id,
    revenue,
    ROUND((cumulative_revenue / total_revenue) * 100, 2) as cumulative_revenue_pct
FROM revenue_percentile
WHERE cumulative_revenue / total_revenue <= 0.80  -- Show top 80% revenue products
ORDER BY rank;

-- ============================================================================
-- 4. CUSTOMER ANALYSIS
-- ============================================================================

-- RFM Segmentation Calculation
WITH customer_metrics AS (
    SELECT 
        customer_id,
        MAX(order_date) as last_order_date,
        COUNT(*) as frequency,
        SUM(price) as monetary,
        CURRENT_DATE - MAX(order_date) as recency
    FROM sales_transactions
    GROUP BY customer_id
),
rfm_scores AS (
    SELECT 
        customer_id,
        recency,
        frequency,
        monetary,
        NTILE(4) OVER (ORDER BY recency DESC) as r_score,
        NTILE(4) OVER (ORDER BY frequency ASC) as f_score,
        NTILE(4) OVER (ORDER BY monetary ASC) as m_score
    FROM customer_metrics
)
SELECT 
    customer_id,
    recency,
    frequency,
    monetary,
    (r_score + f_score + m_score) as rfm_total,
    CASE 
        WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3 THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 2 THEN 'Loyal'
        WHEN r_score <= 2 AND monetary > (SELECT AVG(monetary) FROM customer_metrics) THEN 'At Risk'
        ELSE 'Others'
    END as segment
FROM rfm_scores
ORDER BY monetary DESC;

-- Customer lifetime value (CLV)
SELECT 
    customer_id,
    COUNT(*) as transaction_count,
    SUM(price) as total_spent,
    AVG(price) as avg_transaction,
    MIN(order_date) as first_purchase,
    MAX(order_date) as last_purchase,
    DATEDIFF(day, MIN(order_date), MAX(order_date)) as customer_lifetime_days,
    ROUND(SUM(price) / (DATEDIFF(day, MIN(order_date), CURRENT_DATE) + 1), 2) as daily_avg_value
FROM sales_transactions
GROUP BY customer_id
ORDER BY total_spent DESC;

-- Customer repeat purchase rate
WITH customer_orders AS (
    SELECT 
        customer_id,
        COUNT(DISTINCT DATE(order_date)) as purchase_days
    FROM sales_transactions
    GROUP BY customer_id
)
SELECT 
    SUM(CASE WHEN purchase_days > 1 THEN 1 ELSE 0 END) as repeat_customers,
    SUM(CASE WHEN purchase_days = 1 THEN 1 ELSE 0 END) as one_time_customers,
    COUNT(*) as total_customers,
    ROUND(
        (SUM(CASE WHEN purchase_days > 1 THEN 1 ELSE 0 END)::numeric / COUNT(*)) * 100, 2
    ) as repeat_rate_percentage
FROM customer_orders;

-- ============================================================================
-- 5. STATISTICAL ANALYSIS
-- ============================================================================

-- Descriptive statistics by category
SELECT 
    product_category,
    COUNT(*) as count,
    ROUND(AVG(price), 2) as mean_price,
    ROUND(STDDEV(price), 2) as stddev_price,
    MIN(price) as min_price,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY price) as q1_price,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY price) as median_price,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY price) as q3_price,
    MAX(price) as max_price
FROM sales_transactions
GROUP BY product_category
ORDER BY mean_price DESC;

-- Correlation between order value and customer lifetime
SELECT 
    CORR(price, customer_lifetime_days) as correlation
FROM (
    SELECT 
        price,
        DATEDIFF(day, MIN(order_date) OVER (PARTITION BY customer_id), CURRENT_DATE) as customer_lifetime_days
    FROM sales_transactions
) t;

-- ============================================================================
-- 6. TIME-BASED ANALYSIS
-- ============================================================================

-- Sales by day of week
SELECT 
    TO_CHAR(order_date, 'Day') as day_of_week,
    EXTRACT(DOW FROM order_date) as day_number,
    COUNT(*) as order_count,
    SUM(price) as total_revenue,
    AVG(price) as avg_price
FROM sales_transactions
GROUP BY EXTRACT(DOW FROM order_date), TO_CHAR(order_date, 'Day')
ORDER BY day_number;

-- Seasonality analysis
SELECT 
    EXTRACT(QUARTER FROM order_date) as quarter,
    EXTRACT(MONTH FROM order_date) as month,
    TO_CHAR(order_date, 'Month') as month_name,
    COUNT(*) as order_count,
    SUM(price) as total_revenue,
    ROUND(AVG(price), 2) as avg_price
FROM sales_transactions
GROUP BY EXTRACT(QUARTER FROM order_date), EXTRACT(MONTH FROM order_date), TO_CHAR(order_date, 'Month')
ORDER BY quarter, month;

-- Year-over-year comparison
SELECT 
    EXTRACT(YEAR FROM order_date) as year,
    EXTRACT(MONTH FROM order_date) as month,
    COUNT(*) as order_count,
    SUM(price) as total_revenue
FROM sales_transactions
GROUP BY EXTRACT(YEAR FROM order_date), EXTRACT(MONTH FROM order_date)
ORDER BY year DESC, month;

-- ============================================================================
-- 7. ANOMALY DETECTION
-- ============================================================================

-- Identify outliers (orders > 3 standard deviations from mean)
WITH stats AS (
    SELECT 
        AVG(price) as mean_price,
        STDDEV(price) as std_price
    FROM sales_transactions
)
SELECT 
    order_id,
    customer_id,
    product_id,
    price,
    ROUND((price - (SELECT mean_price FROM stats)) / (SELECT std_price FROM stats), 2) as z_score
FROM sales_transactions, stats
WHERE ABS((price - stats.mean_price) / stats.std_price) > 3
ORDER BY price DESC;

-- Unusual customer behavior (sudden spike in purchases)
WITH customer_daily_orders AS (
    SELECT 
        customer_id,
        DATE(order_date) as order_date,
        COUNT(*) as daily_order_count
    FROM sales_transactions
    GROUP BY customer_id, DATE(order_date)
)
SELECT 
    customer_id,
    order_date,
    daily_order_count,
    AVG(daily_order_count) OVER (PARTITION BY customer_id) as avg_daily_orders
FROM customer_daily_orders
WHERE daily_order_count > 5 * AVG(daily_order_count) OVER (PARTITION BY customer_id)
ORDER BY order_date DESC;

-- ============================================================================
-- 8. COHORT ANALYSIS
-- ============================================================================

-- Customer cohort by acquisition month
WITH first_purchase AS (
    SELECT 
        customer_id,
        DATE_TRUNC('month', MIN(order_date))::DATE as cohort_month
    FROM sales_transactions
    GROUP BY customer_id
),
customer_activity AS (
    SELECT 
        fp.customer_id,
        fp.cohort_month,
        DATE_TRUNC('month', st.order_date)::DATE as activity_month,
        EXTRACT(MONTH FROM AGE(DATE_TRUNC('month', st.order_date)::DATE, fp.cohort_month)) as months_since_acquisition,
        COUNT(*) as transactions,
        SUM(st.price) as revenue
    FROM sales_transactions st
    JOIN first_purchase fp ON st.customer_id = fp.customer_id
    GROUP BY fp.customer_id, fp.cohort_month, DATE_TRUNC('month', st.order_date)::DATE
)
SELECT 
    cohort_month,
    months_since_acquisition,
    COUNT(DISTINCT customer_id) as customers,
    SUM(transactions) as total_transactions,
    ROUND(SUM(revenue), 2) as total_revenue
FROM customer_activity
GROUP BY cohort_month, months_since_acquisition
ORDER BY cohort_month DESC, months_since_acquisition ASC;

-- ============================================================================
-- 9. FORECASTING PREPARATION (Data for forecasting models)
-- ============================================================================

-- Time series data for forecasting
SELECT 
    DATE(order_date) as date,
    COUNT(*) as order_count,
    SUM(price) as daily_revenue,
    COUNT(DISTINCT customer_id) as unique_customers
FROM sales_transactions
GROUP BY DATE(order_date)
ORDER BY date DESC;

-- ============================================================================
-- 10. PERFORMANCE DASHBOARDS QUERIES
-- ============================================================================

-- KPI Summary Dashboard
SELECT 
    (SELECT COUNT(DISTINCT order_id) FROM sales_transactions) as total_orders,
    (SELECT COUNT(DISTINCT customer_id) FROM sales_transactions) as total_customers,
    (SELECT ROUND(SUM(price)::numeric, 2) FROM sales_transactions) as total_revenue,
    (SELECT ROUND(AVG(price)::numeric, 2) FROM sales_transactions) as avg_order_value,
    (SELECT COUNT(DISTINCT product_id) FROM sales_transactions) as unique_products,
    (SELECT COUNT(DISTINCT DATE(order_date)) FROM sales_transactions) as active_days;

-- Top performers summary
SELECT 
    'Top Product' as metric,
    (SELECT product_id FROM sales_transactions GROUP BY product_id ORDER BY SUM(price) DESC LIMIT 1) as value
UNION ALL
SELECT 'Top Customer' as metric,
    (SELECT customer_id FROM sales_transactions GROUP BY customer_id ORDER BY SUM(price) DESC LIMIT 1) as value
UNION ALL
SELECT 'Best Day' as metric,
    (SELECT DATE(order_date)::text FROM sales_transactions GROUP BY DATE(order_date) ORDER BY COUNT(*) DESC LIMIT 1) as value;
