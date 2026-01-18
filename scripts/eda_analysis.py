"""
Data Analyst: EDA and Sales Analysis
Sales Dashboard Analysis for E-Commerce Data
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# 1. DATA LOADING AND BASIC EXPLORATION
# ============================================================================

def load_data(filepath):
    """Load CSV data into pandas DataFrame"""
    df = pd.read_csv(filepath)
    print(f"✓ Data loaded: {len(df)} rows, {len(df.columns)} columns")
    return df

def initial_exploration(df):
    """Perform initial data exploration"""
    print("\n" + "="*60)
    print("DATA OVERVIEW")
    print("="*60)
    print(f"\nShape: {df.shape}")
    print(f"\nColumn Names and Types:\n{df.dtypes}")
    print(f"\nFirst 5 Rows:\n{df.head()}")
    print(f"\nBasic Statistics:\n{df.describe()}")
    print(f"\nMissing Values:\n{df.isnull().sum()}")
    
    return df

# ============================================================================
# 2. DATA CLEANING AND TRANSFORMATION
# ============================================================================

def clean_and_transform(df):
    """Clean and prepare data for analysis"""
    df_clean = df.copy()
    
    # Convert date columns to datetime
    date_columns = [col for col in df_clean.columns if 'date' in col.lower()]
    for col in date_columns:
        df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
    
    # Remove duplicates
    initial_rows = len(df_clean)
    df_clean = df_clean.drop_duplicates()
    print(f"\n✓ Removed {initial_rows - len(df_clean)} duplicate rows")
    
    # Handle missing values
    print(f"\n✓ Missing values before handling:\n{df_clean.isnull().sum()}")
    
    # For numeric columns, fill with median
    numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if df_clean[col].isnull().sum() > 0:
            df_clean[col].fillna(df_clean[col].median(), inplace=True)
    
    # For categorical columns, fill with 'Unknown'
    categorical_cols = df_clean.select_dtypes(include=['object']).columns
    for col in categorical_cols:
        if df_clean[col].isnull().sum() > 0:
            df_clean[col].fillna('Unknown', inplace=True)
    
    print(f"✓ Missing values after handling:\n{df_clean.isnull().sum()}")
    
    return df_clean

# ============================================================================
# 3. EXPLORATORY DATA ANALYSIS (EDA)
# ============================================================================

def analyze_numeric_distributions(df, numeric_cols):
    """Analyze distributions of numeric columns"""
    print("\n" + "="*60)
    print("NUMERIC ANALYSIS")
    print("="*60)
    
    for col in numeric_cols[:5]:  # First 5 numeric columns
        print(f"\n{col}:")
        print(f"  Mean: {df[col].mean():.2f}")
        print(f"  Median: {df[col].median():.2f}")
        print(f"  Std Dev: {df[col].std():.2f}")
        print(f"  Min: {df[col].min():.2f}")
        print(f"  Max: {df[col].max():.2f}")
        print(f"  Skewness: {df[col].skew():.2f}")

def analyze_categorical_distributions(df, categorical_cols):
    """Analyze categorical column distributions"""
    print("\n" + "="*60)
    print("CATEGORICAL ANALYSIS")
    print("="*60)
    
    for col in categorical_cols[:3]:  # First 3 categorical columns
        print(f"\n{col} - Top 10 values:")
        print(df[col].value_counts().head(10))

# ============================================================================
# 4. SALES TRENDS ANALYSIS
# ============================================================================

def monthly_sales_analysis(df, date_col='order_date', amount_col='price'):
    """Analyze sales trends by month"""
    # Extract year-month
    df['year_month'] = pd.to_datetime(df[date_col]).dt.to_period('M')
    
    # Group by month
    monthly_sales = df.groupby('year_month').agg({
        amount_col: ['sum', 'count', 'mean']
    }).reset_index()
    
    monthly_sales.columns = ['Year_Month', 'Total_Revenue', 'Order_Count', 'Avg_Order_Value']
    
    print("\n" + "="*60)
    print("MONTHLY SALES SUMMARY")
    print("="*60)
    print(monthly_sales.to_string(index=False))
    
    return monthly_sales

def identify_top_products(df, product_col='product_category', amount_col='price', top_n=10):
    """Identify top N products by revenue"""
    top_products = df.groupby(product_col).agg({
        amount_col: ['sum', 'count', 'mean']
    }).reset_index()
    
    top_products.columns = [product_col, 'Total_Revenue', 'Order_Count', 'Avg_Price']
    top_products = top_products.sort_values('Total_Revenue', ascending=False).head(top_n)
    
    print("\n" + "="*60)
    print(f"TOP {top_n} PRODUCTS BY REVENUE")
    print("="*60)
    print(top_products.to_string(index=False))
    
    return top_products

# ============================================================================
# 5. CUSTOMER SEGMENTATION (RFM ANALYSIS)
# ============================================================================

def rfm_analysis(df, customer_col='customer_id', date_col='order_date', amount_col='price'):
    """Perform RFM (Recency, Frequency, Monetary) segmentation"""
    
    # Reference date (max date in dataset)
    reference_date = pd.to_datetime(df[date_col]).max() + timedelta(days=1)
    
    rfm = df.groupby(customer_col).agg({
        date_col: lambda x: (reference_date - pd.to_datetime(x).max()).days,
        customer_col: 'count',
        amount_col: 'sum'
    }).reset_index()
    
    rfm.columns = ['customer_id', 'Recency', 'Frequency', 'Monetary']
    
    # Assign R, F, M scores (1-4, where 4 is best)
    rfm['R_Score'] = pd.qcut(rfm['Recency'], q=4, labels=[4,3,2,1], duplicates='drop')
    rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), q=4, labels=[1,2,3,4], duplicates='drop')
    rfm['M_Score'] = pd.qcut(rfm['Monetary'], q=4, labels=[1,2,3,4], duplicates='drop')
    
    # Calculate RFM score
    rfm['RFM_Score'] = rfm['R_Score'].astype(str) + rfm['F_Score'].astype(str) + rfm['M_Score'].astype(str)
    
    # Segment customers
    def segment_customers(row):
        if row['RFM_Score'] == '444':
            return 'Champions'
        elif row['R_Score'] >= 3 and row['F_Score'] >= 3 and row['M_Score'] >= 3:
            return 'Loyal Customers'
        elif row['R_Score'] <= 2 and row['Monetary'] > rfm['Monetary'].median():
            return 'At Risk'
        else:
            return 'Other'
    
    rfm['Segment'] = rfm.apply(segment_customers, axis=1)
    
    print("\n" + "="*60)
    print("RFM SEGMENTATION")
    print("="*60)
    print(rfm['Segment'].value_counts())
    print("\nSegment Summary:")
    print(rfm.groupby('Segment')[['Recency', 'Frequency', 'Monetary']].mean().round(2))
    
    return rfm

# ============================================================================
# 6. CORRELATION AND STATISTICAL ANALYSIS
# ============================================================================

def correlation_analysis(df):
    """Analyze correlations between numeric variables"""
    numeric_df = df.select_dtypes(include=[np.number])
    
    # Calculate correlation matrix
    correlation_matrix = numeric_df.corr()
    
    print("\n" + "="*60)
    print("CORRELATION ANALYSIS")
    print("="*60)
    print(correlation_matrix)
    
    return correlation_matrix

def perform_ab_test(df, control_col, test_col, metric_col):
    """Perform simple A/B test"""
    from scipy import stats
    
    control_group = df[df[control_col] == True][metric_col]
    test_group = df[df[control_col] == False][metric_col]
    
    # T-test
    t_stat, p_value = stats.ttest_ind(control_group, test_group)
    
    print("\n" + "="*60)
    print("A/B TEST RESULTS")
    print("="*60)
    print(f"Control Group Mean: {control_group.mean():.2f}")
    print(f"Test Group Mean: {test_group.mean():.2f}")
    print(f"T-statistic: {t_stat:.4f}")
    print(f"P-value: {p_value:.4f}")
    print(f"Significant (p<0.05): {'Yes' if p_value < 0.05 else 'No'}")
    
    return {'control_mean': control_group.mean(), 'test_mean': test_group.mean(), 'p_value': p_value}

# ============================================================================
# 7. VISUALIZATIONS
# ============================================================================

def create_visualizations(df, monthly_sales, top_products, rfm):
    """Create key visualizations"""
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # 1. Monthly Sales Trend
    ax1 = axes[0, 0]
    monthly_sales['Year_Month'] = monthly_sales['Year_Month'].astype(str)
    ax1.plot(monthly_sales['Year_Month'], monthly_sales['Total_Revenue'], marker='o', linewidth=2)
    ax1.set_title('Monthly Sales Trend', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Month')
    ax1.set_ylabel('Revenue ($)')
    ax1.tick_params(axis='x', rotation=45)
    ax1.grid(True, alpha=0.3)
    
    # 2. Top Products by Revenue
    ax2 = axes[0, 1]
    top_products_sorted = top_products.head(10)
    ax2.barh(range(len(top_products_sorted)), top_products_sorted['Total_Revenue'])
    ax2.set_yticks(range(len(top_products_sorted)))
    ax2.set_yticklabels(top_products_sorted['product_category'])
    ax2.set_title('Top 10 Products by Revenue', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Revenue ($)')
    ax2.invert_yaxis()
    
    # 3. Order Count Distribution
    ax3 = axes[1, 0]
    ax3.bar(monthly_sales['Year_Month'], monthly_sales['Order_Count'], color='skyblue')
    ax3.set_title('Monthly Order Count', fontsize=12, fontweight='bold')
    ax3.set_xlabel('Month')
    ax3.set_ylabel('Number of Orders')
    ax3.tick_params(axis='x', rotation=45)
    ax3.grid(True, alpha=0.3, axis='y')
    
    # 4. RFM Segment Distribution
    ax4 = axes[1, 1]
    segment_counts = rfm['Segment'].value_counts()
    ax4.pie(segment_counts.values, labels=segment_counts.index, autopct='%1.1f%%')
    ax4.set_title('Customer Segmentation (RFM)', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('analysis_dashboard.png', dpi=300, bbox_inches='tight')
    print("\n✓ Visualization saved as 'analysis_dashboard.png'")
    plt.show()

# ============================================================================
# 8. GENERATE INSIGHTS AND RECOMMENDATIONS
# ============================================================================

def generate_insights(df, monthly_sales, top_products, rfm):
    """Generate key insights and recommendations"""
    
    print("\n" + "="*60)
    print("KEY INSIGHTS & RECOMMENDATIONS")
    print("="*60)
    
    # Insight 1: Seasonality
    monthly_revenue = monthly_sales['Total_Revenue'].values
    max_month = monthly_sales.loc[monthly_sales['Total_Revenue'].idxmax(), 'Year_Month']
    min_month = monthly_sales.loc[monthly_sales['Total_Revenue'].idxmin(), 'Year_Month']
    
    print(f"\n1. SEASONALITY ANALYSIS:")
    print(f"   • Peak sales month: {max_month} (${monthly_sales['Total_Revenue'].max():,.0f})")
    print(f"   • Lowest sales month: {min_month} (${monthly_sales['Total_Revenue'].min():,.0f})")
    print(f"   • Seasonal variance: {(monthly_sales['Total_Revenue'].std() / monthly_sales['Total_Revenue'].mean() * 100):.1f}%")
    print(f"   → Recommendation: Adjust inventory and marketing budget by {((monthly_sales['Total_Revenue'].max() - monthly_sales['Total_Revenue'].min()) / monthly_sales['Total_Revenue'].min() * 100):.0f}% across seasons")
    
    # Insight 2: Top Products
    top_20_pct_products = top_products.head(max(1, len(top_products) // 5))
    top_20_pct_revenue = top_20_pct_products['Total_Revenue'].sum()
    total_revenue = top_products['Total_Revenue'].sum()
    revenue_concentration = (top_20_pct_revenue / total_revenue) * 100
    
    print(f"\n2. PRODUCT CONCENTRATION:")
    print(f"   • Top 20% of products generate {revenue_concentration:.1f}% of revenue")
    print(f"   • Top product: {top_products.iloc[0]['product_category']} (${top_products.iloc[0]['Total_Revenue']:,.0f})")
    print(f"   → Recommendation: Focus marketing on top performers and review underperforming products")
    
    # Insight 3: Customer Segmentation
    champions = len(rfm[rfm['Segment'] == 'Champions'])
    loyal = len(rfm[rfm['Segment'] == 'Loyal Customers'])
    at_risk = len(rfm[rfm['Segment'] == 'At Risk'])
    
    print(f"\n3. CUSTOMER SEGMENTATION:")
    print(f"   • Champions: {champions} customers ({champions/len(rfm)*100:.1f}%)")
    print(f"   • Loyal Customers: {loyal} customers ({loyal/len(rfm)*100:.1f}%)")
    print(f"   • At Risk: {at_risk} customers ({at_risk/len(rfm)*100:.1f}%)")
    print(f"   → Recommendation: Implement retention program for at-risk customers and rewards for champions")
    
    # Insight 4: Average Order Value
    aov = df['price'].mean() if 'price' in df.columns else monthly_sales['Avg_Order_Value'].mean()
    print(f"\n4. AVERAGE ORDER VALUE:")
    print(f"   • Current AOV: ${aov:.2f}")
    print(f"   → Recommendation: Consider upselling and cross-selling strategies to increase AOV by 15-20%")

# ============================================================================
# 9. MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("DATA ANALYST - SALES ANALYSIS PROJECT")
    print("="*60)
    
    # Load data
    df = load_data('sales_data.csv')
    
    # Initial exploration
    df = initial_exploration(df)
    
    # Clean and transform
    df_clean = clean_and_transform(df)
    
    # Exploratory Data Analysis
    numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
    categorical_cols = df_clean.select_dtypes(include=['object']).columns
    analyze_numeric_distributions(df_clean, numeric_cols)
    analyze_categorical_distributions(df_clean, categorical_cols)
    
    # Sales Analysis
    monthly_sales = monthly_sales_analysis(df_clean)
    top_products = identify_top_products(df_clean)
    
    # Customer Segmentation
    rfm = rfm_analysis(df_clean)
    
    # Correlation Analysis
    correlation_matrix = correlation_analysis(df_clean)
    
    # Create Visualizations
    create_visualizations(df_clean, monthly_sales, top_products, rfm)
    
    # Generate Insights
    generate_insights(df_clean, monthly_sales, top_products, rfm)
    
    print("\n" + "="*60)
    print("✓ ANALYSIS COMPLETE")
    print("="*60)
