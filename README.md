# ☁️ Cloud-Integrated E-Commerce Big Data Analytics

A cloud-integrated Big Data Analytics project that processes e-commerce sales data using **Amazon S3, AWS EC2, Hadoop HDFS, YARN, Java MapReduce, and Streamlit**.

The system allows users to upload sales data through a Streamlit dashboard, store it in Amazon S3, process it using Hadoop MapReduce on AWS EC2, and visualize the results through an interactive dashboard.

---

## 🚀 Project Workflow

```text
                User
                 │
                 ▼
        ┌─────────────────┐
        │    Streamlit    │
        │    Dashboard    │
        └────────┬────────┘
                 │
                 ▼
        ┌─────────────────┐
        │    Amazon S3    │
        │  Cloud Storage  │
        └────────┬────────┘
                 │
                 ▼
        ┌─────────────────┐
        │     AWS EC2     │
        │  Ubuntu Server  │
        └────────┬────────┘
                 │
                 ▼
        ┌─────────────────┐
        │    Hadoop HDFS  │
        └────────┬────────┘
                 │
                 ▼
        ┌─────────────────┐
        │      YARN       │
        └────────┬────────┘
                 │
                 ▼
        ┌─────────────────┐
        │ Java MapReduce  │
        └────────┬────────┘
                 │
                 ▼
        ┌─────────────────┐
        │    Streamlit    │
        │   Visualization │
        └─────────────────┘