# Troubleshooting Guide

## Common Issues and Solutions

## Backend Issues

### Issue 1: MongoDB SSL/TLS Connection Errors

**Error Message:**
```
ssl.SSLError: [SSL: TLSV1_ALERT_INTERNAL_ERROR] tlsv1 alert internal error
pymongo.errors.AutoReconnect: SSL handshake failed
```

**Root Cause:** Windows SSL library incompatibility with MongoDB Atlas certificates.

**Solution:**

1. Verify MongoDB URI in .env:
   ```
   MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
   ```

2. The backend already includes SSL workarounds:
   - tlsInsecure=True parameter in connection_manager.py
   - Proper timeout configuration
   - Connection pooling with retry logic

3. Test connection:
   ```bash
   cd backend
   python test_mongodb_connection.py
   ```

4. If test passes but app fails:
   - Restart backend server
   - Check .env file has correct MongoDB credentials
   - Ensure MongoDB Atlas cluster is running

5. Still failing? Try:
   ```bash
   # Update SSL certificates
   pip install --upgrade certifi pymongo motor
   
   # Clear Python cache
   rm -rf __pycache__
   rm -rf .pytest_cache
   
   # Reinstall dependencies
   pip install -r requirements.txt
   ```

6. Last resort: Use local MongoDB
   - Install MongoDB Community Edition
   - Change MONGO_URI to: mongodb://localhost:27017/?retryWrites=true&w=majority

---

### Issue 2: "Can't connect to MongoDB"

**Error Message:**
```
pymongo.errors.ServerSelectionTimeoutError: 
[Errno 11001] getaddrinfo failed
```

**Root Cause:** Network timeout or invalid MongoDB URI.

**Solution:**

1. Check MongoDB URI:
   ```bash
   # Verify MONGO_URI in .env doesn't contain placeholders
   grep MONGO_URI .env
   ```

2. Verify MongoDB Atlas cluster is running:
   - Open https://cloud.mongodb.com
   - Check cluster status (should be green)
   - If paused, resume the cluster

3. Check IP whitelist:
   - MongoDB Atlas > Network Access
   - Verify your IP is whitelisted
   - For development: Add 0.0.0.0/0 (any IP)
   - For production: Use specific IP

4. Check network connectivity:
   ```bash
   # Test connection to MongoDB
   ping cluster0.mongodb.net
   
   # Test DNS resolution
   nslookup cluster0.mongodb.net
   ```

5. Increase timeout:
   ```
   MONGO_CONNECTION_TIMEOUT_MS=10000  # 10 seconds instead of 5
   ```

---

### Issue 3: "ModuleNotFoundError: No module named 'fastapi'"

**Error Message:**
```
ModuleNotFoundError: No module named 'fastapi'
ImportError: cannot import name 'FastAPI'
```

**Root Cause:** Python virtual environment not activated or dependencies not installed.

**Solution:**

1. Activate virtual environment (Windows):
   ```bash
   .venv\Scripts\activate
   ```
   Or (macOS/Linux):
   ```bash
   source .venv/bin/activate
   ```

2. Check virtual environment is active:
   - Prompt should show (.venv) prefix
   - Run: `which python` (should show .venv path)

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Verify installation:
   ```bash
   python -c "import fastapi; print(fastapi.__version__)"
   ```

---

### Issue 4: "Port 8000 already in use"

**Error Message:**
```
OSError: [Errno 48] Address already in use
ERROR: Application startup failed
```

**Root Cause:** Another process is using port 8000.

**Solution:**

1. Find process using port 8000 (Windows):
   ```bash
   netstat -ano | findstr :8000
   ```

2. Kill the process:
   ```bash
   taskkill /PID [process_id] /F
   ```

3. Or use different port:
   ```bash
   python -m uvicorn app.main:app --reload --port 8001
   ```

4. On macOS/Linux:
   ```bash
   lsof -i :8000
   kill -9 [process_id]
   ```

---

### Issue 5: "CORS error - No 'Access-Control-Allow-Origin' header"

**Error Message (in browser console):**
```
Access to XMLHttpRequest at 'http://127.0.0.1:8000/api/v1/jobs'
from origin 'http://localhost:5173' has been blocked by CORS policy
```

**Root Cause:** Frontend and backend have different origins not listed in CORS settings.

**Solution:**

1. Check .env CORS_ORIGINS:
   ```
   CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://127.0.0.1:8000
   ```

2. Add your frontend URL:
   - If frontend is on different port: Add to list
   - Separate multiple origins with commas
   - Don't include trailing slashes

3. Restart backend after changing .env:
   ```bash
   # Stop backend (Ctrl+C)
   # Start again
   python -m uvicorn app.main:app --reload
   ```

4. Clear browser cache:
   - Open DevTools (F12)
   - Go to Network tab
   - Right-click and select "Clear browser cache"

---

### Issue 6: "Unrecognized database command: getMore"

**Error Message:**
```
pymongo.errors.OperationFailure: 
'errmsg': 'Unrecognized database command: getMore'
```

**Root Cause:** MongoDB version incompatibility or connection pool issue.

**Solution:**

1. Check MongoDB driver version:
   ```bash
   pip show pymongo motor
   ```

2. Update drivers:
   ```bash
   pip install --upgrade pymongo motor
   ```

3. Reset connection pool:
   - Restart backend server
   - Clear any lingering connections

---

## Frontend Issues

### Issue 7: "npm command not found"

**Error Message:**
```
npm: The term 'npm' is not recognized
```

**Root Cause:** Node.js not installed or not in PATH.

**Solution:**

1. Check Node.js installation:
   ```bash
   node --version
   npm --version
   ```

2. If not installed:
   - Download from https://nodejs.org/
   - Install the LTS version (18 or higher)
   - Restart terminal/PowerShell

3. Add npm to PATH (Windows):
   - Environment Variables > Edit environment variables for your account
   - Add Node.js path: C:\Program Files\nodejs
   - Restart terminal

---

### Issue 8: "Port 5173 already in use"

**Error Message:**
```
Port 5173 is in use, trying 5174...
```

**Root Cause:** Another process is using port 5173.

**Solution:**

1. Allow Vite to use next available port (automatic)
   - Note the port shown: 5174, 5175, etc.

2. Or kill process on port 5173 (Windows):
   ```bash
   netstat -ano | findstr :5173
   taskkill /PID [process_id] /F
   ```

3. Or explicitly use different port:
   ```bash
   npm run dev -- --port 5174
   ```

---

### Issue 9: "WebSocket connection failed"

**Error Message (in browser console):**
```
WebSocket is closed before the connection is established
Failed to connect to WebSocket at ws://127.0.0.1:8000/ws/...
```

**Root Cause:** Backend WebSocket endpoint not running or connection refused.

**Solution:**

1. Verify backend is running:
   - Open http://127.0.0.1:8000/docs
   - Should show API documentation
   - If page not found, backend not running

2. Start backend:
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload
   ```

3. Check WebSocket endpoint:
   - Backend should log: "WebSocket connection accepted"
   - If not, WebSocket handler may have errors

4. Check browser console:
   - Open DevTools (F12)
   - Check Network tab for WebSocket connections
   - Check Console for error messages

5. Clear browser cache and reload

---

### Issue 10: "Blank page or content not loading"

**Symptoms:**
- White/blank screen after opening localhost:5173
- Page loads but no content visible
- CSS not loaded correctly

**Root Cause:** Frontend build issue or CSS not loading.

**Solution:**

1. Clear browser cache:
   - DevTools > Application > Clear storage > Clear all
   - Or use Ctrl+Shift+Delete

2. Hard refresh:
   - Windows: Ctrl+Shift+R
   - macOS: Cmd+Shift+R

3. Check for build errors:
   - Check npm terminal for error messages
   - Look for red error text

4. Rebuild frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

5. Check browser console (F12):
   - Look for JavaScript errors (red text)
   - Check for 404 errors on missing files

6. Verify API connection:
   - Open DevTools > Network
   - Make an action (create job, upload resume)
   - Check API calls - should see requests to 127.0.0.1:8000

---

### Issue 11: "File upload failing"

**Error Message:**
```
Failed to upload resume
Network error during upload
413 Payload Too Large
```

**Root Cause:** File too large or request body too large.

**Solution:**

1. Check file size:
   - Maximum: 10MB for resumes
   - Use PDF format (compression)

2. Increase backend limit (if needed):
   ```python
   # In app/main.py, add to FastAPI initialization:
   app = FastAPI(
       ...
       max_upload_size=26214400  # 25MB
   )
   ```

3. Check NGINX/reverse proxy settings (if deployed)
   ```
   client_max_body_size 25M;
   ```

4. Restart backend and try again

---

### Issue 12: "API returns 404 Not Found"

**Error Message:**
```
404 Not Found: GET /api/v1/jobs
```

**Root Cause:** Endpoint doesn't exist or wrong URL.

**Solution:**

1. Verify backend is running:
   - Check http://127.0.0.1:8000/docs for available endpoints

2. Check API base URL in frontend:
   - Should be: http://127.0.0.1:8000/api/v1
   - Not: http://127.0.0.1:8000/api (missing /v1)

3. Check endpoint exists:
   - Frontend calls: /api/v1/jobs
   - Backend has: @router.get("") → GET /api/v1/jobs

4. Verify no typos in API client:
   - Check api/ folder files
   - Verify endpoint URLs match exactly

---

## Common Workflows

### Test Complete Job Creation Flow

1. Start backend and frontend
2. Open http://localhost:5173
3. Click "Create Job"
4. Enter job title: "Senior Developer"
5. Write job description in "Write Manually"
6. Click "Create & Suggest"
7. Wait for AI suggestions (may take 10-30 seconds)
8. View suggestions and apply one
9. Click "Finalize Job"
10. Submit for vector embedding generation
11. Click "Publish Job"
12. View in "Past Jobs" section

Expected behavior:
- Each step shows loading indicators
- WebSocket events appear in real-time
- Job status changes: DRAFT > REVIEWING > FINALIZED > PUBLISHED
- No errors in browser console

---

### Debug WebSocket Connection

1. Open Browser DevTools (F12)
2. Go to Network tab
3. Filter by "WS" (WebSocket)
4. Perform an action (create job)
5. Look for WebSocket connection
6. Click to view frames sent/received
7. Check for:
   - Connection established (message)
   - Progress updates during AI processing
   - Completion notification

---

### Check Backend Logs

1. Watch backend terminal
2. Each request should show:
   ```
   [request_id] GET /api/v1/jobs/... - 200
   ```

3. Look for errors:
   ```
   ERROR: Failed to create job: [error message]
   ```

4. For debugging:
   ```bash
   # Increase log level
   LOG_LEVEL=DEBUG
   python -m uvicorn app.main:app --reload
   ```

---

## Performance Issues

### Slow Job Creation

**Cause:** AI processing takes time with Google Gemini API.

**Solution:**
- First suggestion takes 10-30 seconds (normal)
- Subsequent calls are faster
- Check API quota: Google Cloud Console > APIs & Services
- Ensure multiple API keys configured for load distribution

### Slow Database Queries

**Cause:** No indexes or large dataset.

**Solution:**
1. Verify MongoDB connection speed:
   ```bash
   python test_mongodb_connection.py
   ```

2. Check query performance:
   - MongoDB Atlas > Performance Advisor
   - Look for recommended indexes

3. Create indexes manually:
   - MongoDB Atlas > Collections
   - Select collection > Indexes tab
   - Add index on frequently queried fields

### Memory Usage Increasing

**Cause:** Memory leaks or large dataset in memory.

**Solution:**
1. Restart backend server periodically
2. Reduce pool size if needed: MONGO_POOL_SIZE=5
3. Clear old activity logs: db.activity_logs.deleteMany({timestamp: {$lt: ISODate("2024-01-01")}})

---

## Getting Help

1. Check this file for your error
2. Check MONGODB_SSL_FIX.md for MongoDB issues
3. Check API_DOCUMENTATION.md for endpoint issues
4. Check backend logs for error messages
5. Check browser console for frontend errors
6. Search Google for specific error message
7. Check GitHub issues for similar problems

---

Last Updated: April 2026
