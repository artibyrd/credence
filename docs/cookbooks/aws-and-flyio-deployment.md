---
title: 'Cookbook: Deploying Credence to AWS and Fly.io'
description: Step-by-step cookbook for hosting sovereign Credence nodes on AWS App Runner, ECS Fargate, or Fly.io with standard Postgres and S3.
since_version: v1.18.0
verified_version: v1.18.0
last_verified: '2026-08-19'
---

# Cookbook: Deploying Credence to AWS and Fly.io

Deploy Credence seamlessly to non-GCP cloud platforms with zero vendor lock-in.

---

## 1. Deploying to Fly.io

```bash
# 1. Launch app with Fly.io CLI
fly launch --image gcr.io/credence-prod-505902/credence-server:latest

# 2. Attach persistent volume for SQLite WAL and local CAS
fly volumes create credence_data --size 10

# 3. Set environment variables
fly secrets set CREDENCE_GEMINI_API_KEY="YOUR_KEY" ENV="production"
```

---

## 2. Deploying to AWS App Runner / ECS

1. Create an AWS App Runner service pointing to your OCI container image.
2. Provide `DATABASE_URL` (AWS RDS PostgreSQL or Aurora Serverless).
3. Provide `S3_BUCKET_NAME` (AWS S3) and `REDIS_URL` (AWS ElastiCache).
