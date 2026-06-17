# VPC Manager

VPC Manager is a lightweight web-based AWS networking management application, that allows authenticated users to create, view, and delete Amazon VPCs and Subnets through a simple dashboard interface.

The application uses AWS Lambda, API Gateway, Cognito, DynamoDB, and EC2 APIs to provide a secure, serverless management experience.
Production Instance
https://main.d1rjl0u4cxd9ib.amplifyapp.com/dashboard.html

Dev Instance
https://dev.d2ruys35orqlu8.amplifyapp.com/dashboard.html

---

## Features

### Authentication

- AWS Cognito User Pool authentication
- Secure JWT-based API authorization
- User login and logout
- Protected API endpoints
- Clean separation din DEV and PROD Environments (deletion is blocked in DEV)
- Deletion is blocked by IAM Policy Role, which can be adjusted in the future.
- Fronted files are automatically deployed using Amplify
- Lambda Python code is automatically updated using Github Actions.
- Git Branch protection using Pull Request Approvers.

### VPC Management

- List VPCs by AWS region
- Create new VPCs
- Delete existing VPCs
- Display VPC Name, ID, CIDR Block, and Region

### Subnet Management

- List subnets within a selected VPC
- Create subnets inside existing VPCs
- CIDR validation
- Overlap detection
- Delete subnets

### Audit Events

- Full audit trail stored in DynamoDB for both  DEV and PROD environments.
- Tracks:
  - Event Type (CREATE / DELETE)
  - Resource Type (VPC / SUBNET)
  - Resource Name
  - Resource ID
  - CIDR Block
  - AWS Region
  - API User
  - Event Timestamp

### User Interface

- Responsive dashboard layout
- Professional card-based design
- Modal dialogs for resource creation
- Scrollable audit event table
- Mobile-friendly layout

---

## Architecture

```text
Browser UI
    |
    v
API Gateway
    |
    v
Lambda Functions
    |
    +---- EC2 API
    |
    +---- DynamoDB
    |
    +---- Cognito
```

---

## Technologies

### Frontend

- HTML5
- CSS3
- JavaScript

### Backend

- AWS Lambda (Python)
- Amazon API Gateway
- Amazon Cognito
- Amazon DynamoDB
- Amazon EC2 SDK (Boto3)
- Amazon Amplify

---

## API Endpoints

### VPCs

GET /vpcs

POST /vpcs

DELETE /vpcs/{vpc_id}

### Subnets

GET /vpcs/{vpc_id}/subnets

POST /vpcs/{vpc_id}/subnets

DELETE /subnets/{subnet_id}

### Audit

GET /audit

DELETE /audit

---

## Security

- Cognito JWT Authentication
- API Gateway Authorizer
- Protected Lambda Endpoints
- Audit Logging
- CORS Configuration

---


