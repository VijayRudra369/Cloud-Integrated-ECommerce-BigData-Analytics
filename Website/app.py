from io import BytesIO
import csv
import io
import os
import re
import subprocess
import tempfile
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="E-Commerce Analytics",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# PROJECT CONFIGURATION
# ============================================================

# CHANGE THIS ONLY IF YOUR AWS S3 BUCKET HAS A DIFFERENT NAME
S3_BUCKET = "vijay-ecommerce-bda-2026"
AWS_REGION = "ap-south-1"

HADOOP_PROJECT = os.path.expanduser(
    "~/ecommerce_mapreduce"
)


# ============================================================
# PAGE DESIGN
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background-color: #0b0f19;
        color: white;
    }

    section[data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #1f2937;
    }

    .metric-card {
        background-color: #131b2e;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 18px 20px;
        min-height: 135px;
    }

    .metric-title {
        color: #94a3b8;
        font-size: 14px;
        font-weight: 500;
    }

    .metric-value {
        color: #ffffff;
        font-size: 24px;
        font-weight: 700;
        margin-top: 5px;
        margin-bottom: 4px;
    }

    .metric-sub {
        color: #64748b;
        font-size: 12px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# COMMAND EXECUTION
# ============================================================

def run_command(command):

    result = subprocess.run(
        command,
        shell=True,
        text=True,
        capture_output=True
    )

    if result.returncode != 0:

        error = (
            result.stderr.strip()
            or result.stdout.strip()
            or "Command failed."
        )

        raise RuntimeError(error)

    return result.stdout.strip()


# ============================================================
# COLUMN NORMALIZATION
# ============================================================

def clean_column_name(name):

    name = str(name)

    name = name.replace("\ufeff", "")

    name = name.strip().lower()

    name = re.sub(
        r"[^a-z0-9]+",
        " ",
        name
    )

    return name.strip()


# ============================================================
# COLUMN ALIASES
# ============================================================

COLUMN_ALIASES = {

    "Product": [
        "product",
        "product name",
        "item",
        "item name",
        "product title",
        "product id"
    ],

    "Category": [
        "category",
        "product category",
        "subcategory"
    ],

    "Quantity": [
        "quantity",
        "quantity ordered",
        "qty",
        "units",
        "units sold",
        "order quantity"
    ],

    "Price": [
        "price",
        "unit price",
        "selling price",
        "sale price",
        "unit cost"
    ],

    "Revenue": [
        "sales",
        "revenue",
        "total sales",
        "sales amount",
        "total revenue",
        "amount"
    ],

    "Date": [
        "date",
        "order date",
        "sale date",
        "transaction date",
        "purchase date"
    ],

    "Customer": [
        "customer",
        "customer name",
        "customer id",
        "buyer",
        "buyer name"
    ],

    "City": [
        "city",
        "customer city",
        "shipping city",
        "billing city",
        "location"
    ]
}


# ============================================================
# FIND COLUMN
# ============================================================

def find_column(df, aliases):

    normalized = {
        column: clean_column_name(column)
        for column in df.columns
    }

    alias_names = [
        clean_column_name(x)
        for x in aliases
    ]

    # Exact match
    for original, value in normalized.items():

        if value in alias_names:
            return original

    # Partial match
    for original, value in normalized.items():

        for alias in alias_names:

            if alias in value or value in alias:
                return original

    return None


# ============================================================
# READ CSV / EXCEL
# ============================================================

def read_uploaded_file(uploaded_file):

    filename = uploaded_file.name.lower()

    # ---------------- CSV ----------------

    if filename.endswith(".csv"):

        raw_bytes = uploaded_file.getvalue()

        if not raw_bytes:

            raise ValueError(
                "The uploaded CSV file is empty."
            )

        encodings = [
            "utf-8-sig",
            "utf-8",
            "cp1252",
            "latin1"
        ]

        text = None

        for encoding in encodings:

            try:

                text = raw_bytes.decode(
                    encoding
                )

                break

            except UnicodeDecodeError:

                continue

        if text is None:

            raise ValueError(
                "Unable to decode the CSV file."
            )

        # Detect delimiter
        try:

            dialect = csv.Sniffer().sniff(
                text[:100000],
                delimiters=",;\t|"
            )

            delimiter = dialect.delimiter

        except csv.Error:

            delimiter = ","

        try:

            df = pd.read_csv(
                io.StringIO(text),
                sep=delimiter,
                engine="python",
                on_bad_lines="warn"
            )

        except Exception:

            df = pd.read_csv(
                io.StringIO(text),
                sep=None,
                engine="python",
                on_bad_lines="warn"
            )

    # ---------------- Excel ----------------

    elif filename.endswith(
        (".xlsx", ".xls")
    ):

        df = pd.read_excel(
            BytesIO(
                uploaded_file.getvalue()
            )
        )

    else:

        raise ValueError(
            "Please upload a CSV or Excel file."
        )

    if df.empty:

        raise ValueError(
            "The uploaded file contains no data."
        )

    return df


# ============================================================
# NORMALIZE DATASET
# ============================================================

def normalize_dataset(df):

    detected = {}

    for target, aliases in COLUMN_ALIASES.items():

        detected[target] = find_column(
            df,
            aliases
        )

    required = [
        "Product",
        "Category",
        "Quantity",
        "Date",
        "Customer",
        "City"
    ]

    missing = [
        column
        for column in required
        if detected[column] is None
    ]

    # Price OR Revenue required
    if (
        detected["Price"] is None
        and detected["Revenue"] is None
    ):

        missing.append(
            "Price/Sales"
        )

    if missing:

        raise ValueError(
            "This dataset is missing required "
            "e-commerce fields: "
            + ", ".join(missing)
        )

    result = pd.DataFrame(
        index=df.index
    )

    # Product
    result["Product"] = (
        df[detected["Product"]]
        .astype(str)
        .str.strip()
    )

    # Category
    result["Category"] = (
        df[detected["Category"]]
        .astype(str)
        .str.strip()
    )

    # Quantity
    result["Quantity"] = pd.to_numeric(

        df[detected["Quantity"]]
        .astype(str)
        .str.replace(
            ",",
            "",
            regex=False
        )
        .str.strip(),

        errors="coerce"
    )

    # Price
    if detected["Price"] is not None:

        result["Price"] = pd.to_numeric(

            df[detected["Price"]]
            .astype(str)
            .str.replace(
                r"[$₹€£,]",
                "",
                regex=True
            )
            .str.strip(),

            errors="coerce"
        )

    else:

        revenue = pd.to_numeric(

            df[detected["Revenue"]]
            .astype(str)
            .str.replace(
                r"[$₹€£,]",
                "",
                regex=True
            )
            .str.strip(),

            errors="coerce"
        )

        result["Price"] = (
            revenue
            /
            result["Quantity"].replace(
                0,
                pd.NA
            )
        )

    # Date
    result["Date"] = pd.to_datetime(
        df[detected["Date"]],
        errors="coerce"
    )

    # Customer
    result["Customer"] = (
        df[detected["Customer"]]
        .astype(str)
        .str.strip()
    )

    # City
    result["City"] = (
        df[detected["City"]]
        .astype(str)
        .str.strip()
    )

    # Remove invalid records
    result = result.dropna(
        subset=[
            "Product",
            "Category",
            "Quantity",
            "Price",
            "Date",
            "Customer",
            "City"
        ]
    )

    result = result[
        result["Quantity"] > 0
    ]

    result = result[
        result["Price"] >= 0
    ]

    result["Quantity"] = (
        result["Quantity"]
        .round()
        .astype(int)
    )

    result["Date"] = (
        result["Date"]
        .dt.strftime("%Y-%m-%d")
    )

    result = result[
        [
            "Product",
            "Category",
            "Quantity",
            "Price",
            "Date",
            "Customer",
            "City"
        ]
    ]

    if result.empty:

        raise ValueError(
            "No valid e-commerce records found."
        )

    return result


# ============================================================
# AWS
# ============================================================

def check_aws():

    run_command(
        "aws sts get-caller-identity"
    )


def upload_s3(local_file, key):

    command = (
        f'aws s3 cp '
        f'"{local_file}" '
        f'"s3://{S3_BUCKET}/{key}" '
        f'--region "{AWS_REGION}"'
    )

    run_command(command)


def download_s3(key, local_file):

    command = (
        f'aws s3 cp '
        f'"s3://{S3_BUCKET}/{key}" '
        f'"{local_file}" '
        f'--region "{AWS_REGION}"'
    )

    run_command(command)


# ============================================================
# HDFS
# ============================================================

def put_hdfs(local_file, hdfs_file):

    directory = os.path.dirname(
        hdfs_file
    )

    run_command(
        f'hdfs dfs -mkdir -p "{directory}"'
    )

    run_command(
        f'hdfs dfs -put -f '
        f'"{local_file}" '
        f'"{hdfs_file}"'
    )


# ============================================================
# MAPREDUCE
# ============================================================

def run_mapreduce(
    jar_name,
    class_name,
    input_path,
    output_path
):

    jar_path = os.path.join(
        HADOOP_PROJECT,
        jar_name
    )

    if not os.path.exists(jar_path):

        raise RuntimeError(
            f"Missing JAR: {jar_path}"
        )

    # Remove old output if present
    subprocess.run(
        f'hdfs dfs -rm -r -f "{output_path}"',
        shell=True,
        text=True,
        capture_output=True
    )

    command = (
        f'cd "{HADOOP_PROJECT}" && '
        f'hadoop jar "{jar_path}" '
        f'{class_name} '
        f'"{input_path}" '
        f'"{output_path}"'
    )

    run_command(command)


# ============================================================
# READ MAPREDUCE OUTPUT
# ============================================================

def read_result(output_path):

    output = run_command(
        f'hdfs dfs -cat '
        f'"{output_path}/part-r-00000"'
    )

    data = {}

    for line in output.splitlines():

        line = line.strip()

        if not line:
            continue

        parts = line.split()

        if len(parts) < 2:
            continue

        key = " ".join(
            parts[:-1]
        )

        try:

            value = float(
                parts[-1]
            )

            data[key] = value

        except ValueError:

            continue

    return data


# ============================================================
# SESSION STATE
# ============================================================

if "analysis_completed" not in st.session_state:

    st.session_state[
        "analysis_completed"
    ] = False


if "current_file" not in st.session_state:

    st.session_state[
        "current_file"
    ] = None


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "### 🛒 E-Commerce Analytics"
    )

    page = st.radio(
        "Navigation",
        [
            "Dashboard",
            "Product Analysis",
            "Category Analysis",
            "City Analysis",
            "Monthly Analysis",
            "Top Products"
        ]
    )

    st.markdown("---")

    st.markdown(
        "#### 📁 Dataset"
    )

    uploaded_file = st.file_uploader(
        "Choose CSV or Excel file",
        type=[
            "csv",
            "xlsx",
            "xls"
        ]
    )

    # Reset results when a new file is selected
    if uploaded_file is not None:

        if (
            st.session_state["current_file"]
            != uploaded_file.name
        ):

            st.session_state[
                "current_file"
            ] = uploaded_file.name

            st.session_state[
                "analysis_completed"
            ] = False

            # Clear previous results
            for key in [
                "product_data",
                "category_data",
                "city_data",
                "monthly_data",
                "top_product_data"
            ]:

                st.session_state.pop(
                    key,
                    None
                )

    st.markdown(
        """
        **Required Columns**

        Product • Category • Quantity •
        Price/Sales • Date • Customer • City
        """
    )

    run_analysis = st.button(
        "▶ Run Analysis",
        use_container_width=True,
        type="primary",
        disabled=uploaded_file is None
    )


# ============================================================
# NO FILE
# ============================================================

if uploaded_file is None:

    st.markdown(
        "## 📊 E-Commerce Sales Analytics"
    )

    st.caption(
        "Turn your sales data into valuable insights"
    )

    st.info(
        "Choose an e-commerce CSV or Excel file "
        "from the sidebar to begin."
    )

    st.stop()


# ============================================================
# READ DATASET
# ============================================================

try:

    source_df = read_uploaded_file(
        uploaded_file
    )

    normalized_df = normalize_dataset(
        source_df
    )

except Exception as error:

    st.error(
        "The uploaded dataset could not be processed."
    )

    st.caption(
        str(error)
    )

    st.stop()


# ============================================================
# WAIT FOR ANALYSIS
# ============================================================

if not st.session_state[
    "analysis_completed"
]:

    st.markdown(
        "## 📊 E-Commerce Sales Analytics"
    )

    st.caption(
        "Turn your sales data into valuable insights"
    )

    st.success(
        f"Dataset ready: {uploaded_file.name}"
    )

    st.write(
        f"Records found: {len(normalized_df)}"
    )

    if not run_analysis:

        st.dataframe(
            normalized_df.head(10),
            use_container_width=True,
            hide_index=True
        )

        st.stop()


# ============================================================
# RUN COMPLETE PIPELINE
# ============================================================

if run_analysis:

    temp_file = None
    downloaded_file = None

    try:

        run_id = datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        )

        safe_name = re.sub(
            r"[^A-Za-z0-9_.-]",
            "_",
            uploaded_file.name
        )

        # ====================================================
        # S3 PATH
        # ====================================================

        s3_key = (
            f"uploads/"
            f"{run_id}_"
            f"{safe_name}"
        )

        # ====================================================
        # HDFS PATH
        # ====================================================

        hdfs_root = (
            f"/ecommerce/runs/{run_id}"
        )

        hdfs_input = (
            f"{hdfs_root}/input/dataset.csv"
        )

        hdfs_output = (
            f"{hdfs_root}/output"
        )

        # ====================================================
        # CREATE NORMALIZED CSV
        # ====================================================

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".csv",
            encoding="utf-8",
            newline="",
            delete=False
        ) as file:

            normalized_df.to_csv(
                file.name,
                index=False
            )

            temp_file = file.name

        progress = st.progress(0)

        status = st.empty()

        # ====================================================
        # AWS CHECK
        # ====================================================

        status.info(
            "Connecting to AWS..."
        )

        check_aws()

        progress.progress(10)

        # ====================================================
        # S3 UPLOAD
        # ====================================================

        status.info(
            "Uploading dataset to Amazon S3..."
        )

        upload_s3(
            temp_file,
            s3_key
        )

        progress.progress(25)

        # ====================================================
        # S3 DOWNLOAD
        # ====================================================

        downloaded_file = (
            f"/tmp/"
            f"{run_id}_dataset.csv"
        )

        status.info(
            "Downloading dataset from Amazon S3..."
        )

        download_s3(
            s3_key,
            downloaded_file
        )

        progress.progress(35)

        # ====================================================
        # HDFS
        # ====================================================

        status.info(
            "Loading dataset into Hadoop HDFS..."
        )

        put_hdfs(
            downloaded_file,
            hdfs_input
        )

        progress.progress(45)

        # ====================================================
        # PRODUCT ANALYSIS
        # ====================================================

        status.info(
            "Running product-wise analysis..."
        )

        run_mapreduce(
            "ProductSales.jar",
            "ProductSales",
            hdfs_input,
            f"{hdfs_output}/product_sales"
        )

        product_data = read_result(
            f"{hdfs_output}/product_sales"
        )

        progress.progress(55)

        # ====================================================
        # CATEGORY ANALYSIS
        # ====================================================

        status.info(
            "Running category-wise analysis..."
        )

        run_mapreduce(
            "CategorySales.jar",
            "CategorySales",
            hdfs_input,
            f"{hdfs_output}/category_sales"
        )

        category_data = read_result(
            f"{hdfs_output}/category_sales"
        )

        progress.progress(65)

        # ====================================================
        # CITY ANALYSIS
        # ====================================================

        status.info(
            "Running city-wise analysis..."
        )

        run_mapreduce(
            "CitySales.jar",
            "CitySales",
            hdfs_input,
            f"{hdfs_output}/city_sales"
        )

        city_data = read_result(
            f"{hdfs_output}/city_sales"
        )

        progress.progress(75)

        # ====================================================
        # MONTHLY ANALYSIS
        # ====================================================

        status.info(
            "Running monthly sales analysis..."
        )

        run_mapreduce(
            "MonthlySales.jar",
            "MonthlySales",
            hdfs_input,
            f"{hdfs_output}/monthly_sales"
        )

        monthly_data = read_result(
            f"{hdfs_output}/monthly_sales"
        )

        progress.progress(85)

        # ====================================================
        # TOP PRODUCTS
        # ====================================================

        status.info(
            "Running top-selling products analysis..."
        )

        run_mapreduce(
            "TopProducts.jar",
            "TopProducts",
            hdfs_input,
            f"{hdfs_output}/top_products"
        )

        top_product_data = read_result(
            f"{hdfs_output}/top_products"
        )

        progress.progress(100)

        # ====================================================
        # SAVE RESULTS
        # ====================================================

        st.session_state[
            "product_data"
        ] = product_data

        st.session_state[
            "category_data"
        ] = category_data

        st.session_state[
            "city_data"
        ] = city_data

        st.session_state[
            "monthly_data"
        ] = monthly_data

        st.session_state[
            "top_product_data"
        ] = top_product_data

        st.session_state[
            "analysis_completed"
        ] = True

        status.success(
            "Analysis completed successfully."
        )

        # Cleanup
        for path in [
            temp_file,
            downloaded_file
        ]:

            if (
                path
                and os.path.exists(path)
            ):

                try:

                    os.remove(path)

                except OSError:

                    pass

        st.rerun()

    except Exception as error:

        st.error(
            "Analysis failed."
        )

        st.exception(error)

        # Cleanup
        for path in [
            temp_file,
            downloaded_file
        ]:

            if (
                path
                and os.path.exists(path)
            ):

                try:

                    os.remove(path)

                except OSError:

                    pass

        st.stop()


# ============================================================
# GET RESULTS
# ============================================================

product_data = st.session_state.get(
    "product_data",
    {}
)

category_data = st.session_state.get(
    "category_data",
    {}
)

city_data = st.session_state.get(
    "city_data",
    {}
)

monthly_data = st.session_state.get(
    "monthly_data",
    {}
)

top_product_data = st.session_state.get(
    "top_product_data",
    {}
)


# ============================================================
# DATAFRAMES
# ============================================================

product_df = pd.DataFrame(
    list(product_data.items()),
    columns=[
        "Product",
        "Revenue"
    ]
).sort_values(
    "Revenue",
    ascending=False
)


category_df = pd.DataFrame(
    list(category_data.items()),
    columns=[
        "Category",
        "Revenue"
    ]
).sort_values(
    "Revenue",
    ascending=False
)


city_df = pd.DataFrame(
    list(city_data.items()),
    columns=[
        "City",
        "Revenue"
    ]
).sort_values(
    "Revenue",
    ascending=False
)


monthly_df = pd.DataFrame(
    list(monthly_data.items()),
    columns=[
        "Month",
        "Revenue"
    ]
).sort_values(
    "Month"
)


top_products_df = pd.DataFrame(
    list(top_product_data.items()),
    columns=[
        "Product",
        "Quantity"
    ]
).sort_values(
    "Quantity",
    ascending=False
).head(5)


top_products_df.insert(
    0,
    "Rank",
    range(
        1,
        len(top_products_df) + 1
    )
)


if not top_products_df.empty:

    top_products_df[
        "Quantity"
    ] = (
        top_products_df[
            "Quantity"
        ]
        .round()
        .astype(int)
    )


# ============================================================
# KPI VALUES
# ============================================================

total_revenue = (
    sum(product_data.values())
    if product_data
    else 0
)

units_sold = (
    sum(top_product_data.values())
    if top_product_data
    else 0
)

top_product = (
    max(
        product_data,
        key=product_data.get
    )
    if product_data
    else "N/A"
)

top_city = (
    max(
        city_data,
        key=city_data.get
    )
    if city_data
    else "N/A"
)


# ============================================================
# DASHBOARD
# ============================================================

if page == "Dashboard":

    header_left, header_right = st.columns(
        [4, 1]
    )

    with header_left:

        st.markdown(
            "## 📊 E-Commerce Sales Analytics"
        )

        st.caption(
            "Turn your sales data into valuable insights"
        )

    with header_right:

        st.markdown(
            "### 🟢 Analysis Completed"
        )

    # ========================================================
    # KPI CARDS
    # ========================================================

    m1, m2, m3, m4 = st.columns(4)

    with m1:

        st.markdown(
            f"""
            <div class="metric-card">

                <div class="metric-title">
                    Total Revenue
                </div>

                <div class="metric-value">
                    ₹ {total_revenue:,.0f}
                </div>

                <div class="metric-sub">
                    Total sales revenue
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    with m2:

        st.markdown(
            f"""
            <div class="metric-card">

                <div class="metric-title">
                    Units Sold
                </div>

                <div class="metric-value">
                    {units_sold:,.0f}
                </div>

                <div class="metric-sub">
                    Total quantity sold
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    with m3:

        st.markdown(
            f"""
            <div class="metric-card">

                <div class="metric-title">
                    Top Product
                </div>

                <div class="metric-value">
                    {top_product}
                </div>

                <div class="metric-sub">
                    Highest revenue
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    with m4:

        st.markdown(
            f"""
            <div class="metric-card">

                <div class="metric-title">
                    Top City
                </div>

                <div class="metric-value">
                    {top_city}
                </div>

                <div class="metric-sub">
                    Highest sales
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown(
        "<br>",
        unsafe_allow_html=True
    )

    # ========================================================
    # PRODUCT + CATEGORY
    # ========================================================

    col1, col2 = st.columns(2)

    # PRODUCT
    with col1:

        st.markdown(
            "### 📊 Product-wise Revenue"
        )

        fig_product = px.bar(
            product_df,
            x="Product",
            y="Revenue",
            text="Revenue",
            color="Product"
        )

        fig_product.update_traces(
            texttemplate="₹%{text:,.0f}",
            textposition="outside",
            cliponaxis=False
        )

        fig_product.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
            showlegend=False,
            xaxis=dict(
                title="",
                showgrid=False
            ),
            yaxis=dict(
                title="",
                showgrid=False,
                visible=False
            ),
            height=320,
            margin=dict(
                l=10,
                r=10,
                t=20,
                b=10
            )
        )

        st.plotly_chart(
            fig_product,
            use_container_width=True
        )

    # CATEGORY
    with col2:

        st.markdown(
            "### 👛 Category-wise Revenue"
        )

        fig_category = go.Figure(
            data=[
                go.Pie(
                    labels=category_df[
                        "Category"
                    ],
                    values=category_df[
                        "Revenue"
                    ],
                    hole=0.6,
                    textinfo="percent",
                    hoverinfo="label+value+percent"
                )
            ]
        )

        fig_category.add_annotation(
            text=(
                f"<b>Total Revenue</b>"
                f"<br>₹{total_revenue:,.0f}"
            ),
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(
                color="white",
                size=12
            )
        )

        fig_category.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
            height=320,
            margin=dict(
                l=10,
                r=10,
                t=10,
                b=10
            )
        )

        st.plotly_chart(
            fig_category,
            use_container_width=True
        )

    # ========================================================
    # CITY + MONTHLY + TOP PRODUCTS
    # ========================================================

    col3, col4, col5 = st.columns(3)

    # CITY
    with col3:

        st.markdown(
            "### 📍 City-wise Revenue"
        )

        fig_city = px.bar(
            city_df.sort_values(
                "Revenue",
                ascending=True
            ),
            y="City",
            x="Revenue",
            orientation="h",
            text="Revenue",
            color="City"
        )

        fig_city.update_traces(
            texttemplate="₹%{text:,.0f}",
            textposition="outside",
            cliponaxis=False
        )

        fig_city.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
            showlegend=False,
            xaxis=dict(
                title="",
                showgrid=False,
                visible=False
            ),
            yaxis=dict(
                title="",
                showgrid=False
            ),
            height=300,
            margin=dict(
                l=10,
                r=10,
                t=20,
                b=10
            )
        )

        st.plotly_chart(
            fig_city,
            use_container_width=True
        )

    # MONTHLY
    with col4:

        st.markdown(
            "### 📈 Monthly Revenue Trend"
        )

        fig_monthly = px.line(
            monthly_df,
            x="Month",
            y="Revenue",
            markers=True
        )

        fig_monthly.update_traces(
            line=dict(
                width=3
            ),
            marker=dict(
                size=7
            )
        )

        fig_monthly.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
            xaxis=dict(
                title="",
                showgrid=False
            ),
            yaxis=dict(
                title="",
                showgrid=True
            ),
            height=300,
            margin=dict(
                l=10,
                r=10,
                t=20,
                b=10
            )
        )

        st.plotly_chart(
            fig_monthly,
            use_container_width=True
        )

    # TOP PRODUCTS
    with col5:

        st.markdown(
            "### 👑 Top 5 Products by Quantity"
        )

        st.dataframe(
            top_products_df,
            hide_index=True,
            use_container_width=True,
            height=270
        )


# ============================================================
# INDIVIDUAL ANALYSIS PAGES
# ============================================================

elif page == "Product Analysis":

    st.header(
        "📊 Product Analysis"
    )

    st.bar_chart(
        product_df.set_index(
            "Product"
        )
    )


elif page == "Category Analysis":

    st.header(
        "👛 Category Analysis"
    )

    st.bar_chart(
        category_df.set_index(
            "Category"
        )
    )


elif page == "City Analysis":

    st.header(
        "📍 City Analysis"
    )

    st.bar_chart(
        city_df.set_index(
            "City"
        )
    )


elif page == "Monthly Analysis":

    st.header(
        "📈 Monthly Analysis"
    )

    st.line_chart(
        monthly_df.set_index(
            "Month"
        )
    )


elif page == "Top Products":

    st.header(
        "👑 Top Products"
    )

    st.dataframe(
        top_products_df,
        use_container_width=True,
        hide_index=True
    )