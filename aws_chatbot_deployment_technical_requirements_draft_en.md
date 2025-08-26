# AWS Chatbot Deployment – Technical Requirements Draft (Updated)

## 1 Objective
Deploy a **minimum viable chatbot (MVP)** that allows users to enter questions in a browser, forwards the request to AWS Bedrock for inference, returns the answer, and stores the conversation log.

---

## 2 High‑Level Architecture
```
Browser
   │ HTTPS
S3 (static website hosting)
   │ HTTPS (REST)
Amazon API Gateway
   │ Lambda Proxy
AWS Lambda ────▶ Bedrock InvokeModel
   │
[Future: Amazon DynamoDB for session store]
```

---

## 3 Work Breakdown
### 3.1 Front‑End
- **Stack:** HTML + CSS + JavaScript (Vanilla JS)
- **Features:** input box, call `POST /chat`, render response, error handling, basic chat interface
- **Hosting:** S3 static website

### 3.2 Back‑End
- **Lambda**
  - Validate request and handle CORS
  - Call Bedrock Claude 3.5 Sonnet model and return JSON response
  - Basic error handling and logging
  - Future: persist Q&A pairs to DynamoDB
- Future: **state machine?**

### 3.3 API Gateway
- **Protocol:** REST (HTTP/JSON) with CORS support
- **Auth (MVP):** open / anonymous. Add Cognito or enterprise OIDC for production
- **Endpoint:** `/chat` POST method

### 3.4 Data Storage
- **Current:** In-memory conversation handling (stateless)
- **Future:** DynamoDB integration
  - PK: `session_id` + `timestamp` (sort key)
  - Attributes: `role`, `content`
  - TTL to auto‑expire old items and save cost

### 3.5 Infrastructure as Code
- Use **AWS SAM (Serverless Application Model)** to generate CloudFormation:
  - S3, API Gateway, Lambda
  - IAM roles with least privilege for Bedrock access
  - Basic CloudWatch Logs
  - Future: DynamoDB, enhanced monitoring

---

## 4 Non‑Functional Requirements
| Category | Requirement |
| --- | --- |
| **Security** | HTTPS for all traffic; IAM least privilege for Bedrock; CORS properly configured |
| **Observability** | CloudWatch Logs (basic), Lambda execution metrics |
| **Scalability** | Lambda auto-scaling, S3 static hosting |
| **Cost** | Pay‑as‑you‑go components; monitor Bedrock token spend |
| **Compliance** | Basic encryption in transit; CloudWatch log retention |

---

## 5 Deliverables
1. Architecture diagram (PNG + editable source)
2. SAM project repository with template.yaml
3. Front‑end source code (HTML/JS)
4. README with deployment steps & environment configuration
5. Deployment scripts and Makefile
6. Environment-specific configurations (dev/staging/prod)

---

## 6 Open Questions / Pending Decisions
| Topic | Options |
| --- | --- |
| Front‑end framework | Current: Vanilla JS, Future: React consideration |
| Session storage | Current: Stateless, Future: DynamoDB vs Aurora Serverless |
| Authentication | Current: Anonymous, Future: Cognito vs Enterprise SSO |
| Session storage | Current: Stateless, Future: DynamoDB vs Aurora Serverless |
| Monitoring | Current: Basic CloudWatch, Future: Enhanced metrics & alerts |

---

## 7 Risks & Recommendations
- **Current State:** MVP is functional but lacks persistence and advanced features
- **Data Persistence:** Implement DynamoDB integration early to avoid data loss
- **Performance:** Optimize Lambda cold start and response times
- **Monitoring:** Enhance CloudWatch metrics and set up basic alarms
- **Security:** Current CORS is permissive (`*`) - restrict for production
- **Cost Control:** Set up Bedrock usage monitoring and budget alerts
- **Future Planning:** Design for easy migration from SAM to CDK if needed

---

## 8 Current Implementation Status
- ✅ **Completed:** Basic Lambda + API Gateway + S3 setup
- ✅ **Completed:** Claude 3.5 Sonnet integration
- ✅ **Completed:** Multi-environment deployment (dev/staging/prod)
- ✅ **Completed:** Basic CORS and error handling
- 🔄 **In Progress:** Enhanced monitoring and logging
- ❌ **Not Started:** DynamoDB integration

- ❌ **Not Started:** Advanced security features

---

> **Next Step:** Review current implementation; prioritize DynamoDB integration and enhanced monitoring before adding new features.

