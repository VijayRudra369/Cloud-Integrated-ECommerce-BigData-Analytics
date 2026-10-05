# ☁️ Cloud-Integrated E-Commerce Big Data Analytics

> An end-to-end Big Data Analytics project integrating **AWS Cloud, Hadoop, MapReduce, and Streamlit** for e-commerce sales analysis.

## 📌 Overview

This project demonstrates how e-commerce sales data can be stored in the cloud, processed using Hadoop MapReduce, and presented through an interactive web dashboard.

The application uses **Amazon S3** for cloud storage and **AWS EC2** as the processing and deployment environment. Hadoop **HDFS** stores the dataset, **YARN** manages the processing resources, and five Java **MapReduce** programs perform the required analytics.

The final results are displayed through a **Streamlit dashboard**.

---

## 🏗️ System Architecture

```text
                    ┌──────────────┐
                    │     User     │
                    └──────┬───────┘
                           │
                           ▼
                 ┌──────────────────┐
                 │    Streamlit     │
                 │    Dashboard     │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │    Amazon S3     │
                 │  Cloud Storage   │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │     AWS EC2      │
                 │  Ubuntu Server   │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │    Hadoop HDFS   │
                 │  Data Storage    │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │      YARN        │
                 │ Resource Manager │
                 └────────┬─────────┘
                          │
                          ▼
              ┌─────────────────────────┐
              │    Java MapReduce       │
              ├─────────────────────────┤
              │ Product Sales           │
              │ Category Sales          │
              │ City Sales              │
              │ Monthly Sales           │
              │ Top Products            │
              └────────────┬────────────┘
                           │
                           ▼
                 ┌──────────────────┐
                 │    Streamlit     │
                 │  Visualization   │
                 └──────────────────┘