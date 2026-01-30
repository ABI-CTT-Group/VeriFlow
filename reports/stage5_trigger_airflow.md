# Stage 5: Airflow DAG Trigger Guide

**Purpose**: Manually trigger and verify Airflow DAG execution  
**Prerequisites**: Docker Compose running with Airflow services

---

## Method 1: Web UI (Recommended)

### Step 1: Access Airflow Web UI

1. Open your browser and navigate to: **http://localhost:8080**
2. Login with credentials:
   - **Username**: `airflow`
   - **Password**: `airflow`

### Step 2: Find the Template DAG

1. On the DAGs page, look for `veriflow_template`
2. If the DAG shows as "paused" (toggle is gray), click the toggle to unpause it

### Step 3: Trigger the DAG

1. Click on the DAG name `veriflow_template` to open DAG details
2. Click the **"Play" button** (▶️) in the top right corner
3. Select **"Trigger DAG"** from the dropdown menu
4. In the popup dialog:
   - You can leave the configuration JSON empty `{}`
   - Or add custom config if needed
5. Click **"Trigger"** to start the DAG run

### Step 4: Monitor Execution

1. After triggering, a new DAG run will appear in the runs list
2. Click on the run to see the **Graph View** or **Grid View**
3. Watch the task status progression:
   - ⬜ White = Not started (scheduled)
   - 🟡 Yellow/Orange = Running
   - 🟢 Green = Success
   - 🔴 Red = Failed

### Step 5: View Task Logs

1. Click on any task box in the Graph View
2. Select **"Log"** from the popup
3. Review the logs to verify execution

---

## Method 2: REST API (PowerShell)

### Trigger DAG via API

```powershell
# Set up authentication
$auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("airflow:airflow"))
$headers = @{
    "Content-Type" = "application/json"
    "Authorization" = "Basic $auth"
}

# Trigger the DAG
Invoke-RestMethod `
    -Uri "http://localhost:8080/api/v1/dags/veriflow_template/dagRuns" `
    -Method POST `
    -Headers $headers `
    -Body '{}'
```

### Check DAG Run Status

```powershell
# Get the latest DAG run
$runs = Invoke-RestMethod `
    -Uri "http://localhost:8080/api/v1/dags/veriflow_template/dagRuns" `
    -Method GET `
    -Headers $headers

# Display run info
$runs.dag_runs | Select-Object dag_run_id, state, start_date | Format-Table
```

### Get Task Instance Status

```powershell
# Replace {dag_run_id} with actual run ID from previous command
$runId = "manual__2026-01-30T00:00:00+00:00"

$tasks = Invoke-RestMethod `
    -Uri "http://localhost:8080/api/v1/dags/veriflow_template/dagRuns/$runId/taskInstances" `
    -Method GET `
    -Headers $headers

$tasks.task_instances | Select-Object task_id, state, duration | Format-Table
```

---

## Method 3: CLI (Inside Container)

```bash
# Enter the Airflow container
docker exec -it veriflow-airflow-webserver bash

# Trigger DAG
airflow dags trigger veriflow_template

# List recent DAG runs
airflow dags list-runs -d veriflow_template

# Check task status
airflow tasks list veriflow_template
```

---

## Verification Checklist

| Check | Expected Result |
|-------|-----------------|
| DAG appears in UI | `veriflow_template` visible in DAGs list |
| DAG can be triggered | Run starts within a few seconds |
| Tasks execute | All tasks turn green |
| Logs available | Task logs show output |
| No errors | No red (failed) tasks |

---

## Troubleshooting

### DAG Not Appearing

1. Check if Airflow scheduler is running:
   ```powershell
   docker ps | Select-String "airflow"
   ```

2. Check scheduler logs:
   ```powershell
   docker logs veriflow-airflow-scheduler --tail 50
   ```

3. Verify DAG file exists:
   ```powershell
   Get-ChildItem .\dags\
   ```

4. Wait 30 seconds - Airflow scans DAGs folder periodically

### DAG Trigger Fails

1. Check webserver logs:
   ```powershell
   docker logs veriflow-airflow-webserver --tail 50
   ```

2. Verify database connection:
   ```powershell
   docker exec veriflow-airflow-webserver airflow db check
   ```

### Tasks Fail

1. Click on the failed task in the UI
2. View the logs for error details
3. Common issues:
   - Docker not available inside Airflow container
   - Missing environment variables
   - Network connectivity issues

---

## Expected Workflow

```
┌─────────┐     ┌─────────┐
│  start  │ ──► │   end   │
└─────────┘     └─────────┘
```

The template DAG has two simple `EmptyOperator` tasks:
- `start` → `end`

Both should complete immediately (within 1 second).

---

## Next Steps

After verifying the template DAG works:

1. ✅ Confirm DAG appears in Airflow UI
2. ✅ Confirm DAG can be triggered
3. ✅ Confirm tasks execute successfully
4. ➡️ Proceed to Stage 6: End-to-End Integration
