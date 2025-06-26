import pandas as pd
import numpy as np
import io
import logging
import traceback
from scipy import stats
from datetime import datetime
from azure.storage.filedatalake import DataLakeServiceClient
from azure.data.tables import TableServiceClient
import json
from io import StringIO

# ✅ Logging config
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def load_data_from_adls(account_name, account_key, file_system, file_path):
    print(f"📥 Loading from ADLS - Container: {file_system}, File: {file_path}")
    try:
        service_client = DataLakeServiceClient(
            account_url=f"https://{account_name}.dfs.core.windows.net",
            credential=account_key
        )

        file_system_client = service_client.get_file_system_client(file_system)
        file_client = file_system_client.get_file_client(file_path)

        download = file_client.download_file()
        content = download.readall()

        df = pd.read_csv(io.BytesIO(content))
        print(f"✅ Loaded {len(df)} rows from {file_path}")
        return df

    except Exception as e:
        print(f"❌ Error reading from ADLS: {e}")
        raise

def join_data(transactions_df, products_df):
    transactions_df = transactions_df.rename(columns={"product_id": "ProductID"})
    products_df = products_df.rename(columns={
        "product_id": "ProductID",
        "product_name": "ProductName",
        "category": "Category",
        "price": "Price"
    })

    merged_df = pd.merge(transactions_df, products_df, on="ProductID", how="left")
    merged_df = merged_df.rename(columns={"customer_id": "CustomerID"})

    merged_df['quantity'] = pd.to_numeric(merged_df['quantity'], errors='coerce')
    merged_df['Price'] = pd.to_numeric(merged_df['Price'], errors='coerce')
    merged_df['Amount'] = merged_df['quantity'] * merged_df['Price']

    merged_df = merged_df.dropna(subset=['Amount'])
    merged_df['Category'] = merged_df['Category'].fillna('Unknown')

    return merged_df

def analyze_data(df):
    try:
        insights = {}

        if 'Category' in df.columns:
            top_categories = df['Category'].value_counts().head(5).to_dict()
            insights['topCategories'] = [{"category": k, "count": v} for k, v in top_categories.items()]
        else:
            insights['topCategories'] = []

        if 'campaign_id' in df.columns and 'Amount' in df.columns:
            campaign_impact = df.groupby('campaign_id')['Amount'].agg(['sum', 'mean', 'count']).round(2)
            insights['campaignImpact'] = [
                {
                    "campaignId": idx,
                    "totalRevenue": row['sum'],
                    "avgRevenue": row['mean'],
                    "orderCount": row['count']
                }
                for idx, row in campaign_impact.iterrows()
            ]
        else:
            insights['campaignImpact'] = []

        missing_values = df.isnull().sum()
        insights['missingValues'] = [
            {"column": col, "missing_count": count, "percentage": round((count/len(df))*100, 2)}
            for col, count in missing_values.items() if count > 0
        ]

        numeric_columns = df.select_dtypes(include=[np.number]).columns
        outliers_info = []
        for col in numeric_columns:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR
            count = len(df[(df[col] < lower) | (df[col] > upper)])
            if count > 0:
                outliers_info.append({
                    "column": col,
                    "outlier_count": count,
                    "percentage": round((count/len(df))*100, 2),
                    "lower_bound": round(lower, 2),
                    "upper_bound": round(upper, 2)
                })
        insights['outliers'] = outliers_info

        if 'CustomerID' in df.columns and 'Amount' in df.columns:
            aov_data = df.groupby('CustomerID')['Amount'].mean().round(2)
            insights['aovData'] = [
                {"CustomerID": str(cust), "AvgOrderValue": float(aov)}
                for cust, aov in aov_data.items()
            ]
        else:
            insights['aovData'] = []

        if 'ProductName' in df.columns:
            top_products = df['ProductName'].value_counts().head(5)
            insights['topProducts'] = [
                {"product": product, "totalSold": int(count)}
                for product, count in top_products.items()
            ]
        else:
            insights['topProducts'] = []

        insights['recommendations'] = generate_recommendations(df, insights)
        insights['success'] = True
        return insights

    except Exception as e:
        logger.error(f"Error in analyze_data: {str(e)}")
        logger.error(traceback.format_exc())
        raise e

def generate_recommendations(df, insights):
    recommendations = []
    try:
        if insights.get('campaignImpact'):
            best = max(insights['campaignImpact'], key=lambda x: x['totalRevenue'])
            recommendations.append({
                "type": "campaign",
                "priority": "high",
                "message": f"Campaign {best['campaignId']} generated highest revenue: ₹{int(best['totalRevenue']):,}."
            })

        if insights.get('missingValues'):
            high_missing = [x for x in insights['missingValues'] if x['percentage'] > 10]
            if high_missing:
                recommendations.append({
                    "type": "data_quality",
                    "priority": "medium",
                    "message": "Several columns have >10% missing values. Consider cleaning."
                })

        if insights.get('outliers'):
            recommendations.append({
                "type": "outliers",
                "priority": "low",
                "message": f"Detected outliers in {len(insights['outliers'])} columns."
            })

        if insights.get('topProducts'):
            top = insights['topProducts'][0]
            recommendations.append({
                "type": "sales",
                "priority": "high",
                "message": f"'{top['product']}' is best-selling with {top['totalSold']} sales. Promote it."
            })

        return recommendations

    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        return [{"type": "error", "priority": "low", "message": "Could not generate recommendations."}]

def store_insights(insights, account_name, account_key, container_name, base_path):
    try:
        date_str = datetime.now().strftime("%Y%m%d")
        directory_path = f"{base_path}/v{date_str}"
        file_name = "insights.json"

        service_client = DataLakeServiceClient(
            account_url=f"https://{account_name}.dfs.core.windows.net",
            credential=account_key
        )
        file_system_client = service_client.get_file_system_client(container_name)
        directory_client = file_system_client.get_directory_client(directory_path)

        if not directory_client.exists():
            directory_client.create_directory()

        insights_json = json.dumps(insights)
        file_client = directory_client.get_file_client(file_name)
        file_client.upload_data(insights_json, overwrite=True)

    except Exception as e:
        print(f"Error storing insights: {str(e)}")
        raise

def save_contact_submission(connection_string, table_name, name, email, message):
    try:
        table_service = TableServiceClient.from_connection_string(connection_string)
        table_client = table_service.get_table_client(table_name)

        entity = {
            "PartitionKey": "contact",
            "RowKey": str(datetime.now().timestamp()),
            "Name": name,
            "Email": email,
            "Message": message
        }
        table_client.create_entity(entity)

    except Exception as e:
        print(f"Error saving contact submission: {str(e)}")
        raise
