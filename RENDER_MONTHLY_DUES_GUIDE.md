# Render Monthly Dues System Guide (Free Tier)

## 🚀 **How Render Runs the Monthly Dues System (Free Tier)**

### **1. Start Command**
```bash
flask db upgrade && gunicorn --bind 0.0.0.0:$PORT run:app
```

This command:
- Runs database migrations (`flask db upgrade`)
- Starts the Flask app with Gunicorn on the specified port

### **2. Manual Monthly Dues Assignment (Free Tier)**

Since **cron jobs are not available on free tier**, you have these options:

#### **Option A: Manual Trigger Button (Recommended)**
- **Location**: Admin Panel → Fee Management → "Assign Monthly Dues" button
- **What it does**: Assigns monthly dues for all students with one click
- **When to use**: On the 1st of each month (or whenever needed)

#### **Option B: Manual Script Execution**
```bash
# Run the monthly dues manager
python scripts/monthly_dues_manager.py
# Choose option 2: Run Monthly Dues Assignment
```

#### **Option C: Force Assignment**
```bash
# Force assign all dues (ignores schedule setting)
python scripts/monthly_dues_manager.py
# Choose option 3: Force Assign All Dues
```

## 📅 **How the System Works**

### **For Existing Students (Joined Before Current Month)**
- ✅ **Get dues when manually triggered**
- ✅ **Example**: Student joined in May 2025 → Gets June 2025 due when you click the button

### **For New Students (Joined in Current Month)**
- ✅ **Get dues immediately upon joining**
- ✅ **Example**: Student joins on June 15, 2025 → Gets June 2025 due immediately

### **Manual Trigger Logic**
```python
# When you click "Assign Monthly Dues" button:
# - Existing students get current month dues
# - New students already have current month dues
# - No duplicate dues are created
```

## ⚙️ **Configuration Options**

### **1. Enable/Disable Scheduling**
- **Admin Panel**: Go to UPI Settings → Scheduled Monthly Dues
- **Note**: On free tier, this setting controls the manual trigger behavior

### **2. Set Monthly Due Amount**
- **Admin Panel**: Go to UPI Settings → Monthly Due Amount
- **Default**: ₹1500
- **Range**: Any amount you set

### **3. Manual Assignment**
- **Admin Panel**: Fee Management → "Assign Monthly Dues" button
- **Script**: `python scripts/monthly_dues_manager.py`

## 🔧 **Free Tier Deployment Steps**

### **1. Deploy with render.yaml**
```yaml
services:
  - type: web
    name: excellence-tutorial-app
    startCommand: "flask db upgrade && gunicorn --bind 0.0.0.0:$PORT run:app"
  - type: postgres
    name: excellence-tutorial-db
    plan: free
```

### **2. Set Environment Variables**
In Render Dashboard:
- `DATABASE_URL`: Auto-set from PostgreSQL
- `FLASK_ENV`: `production`
- `EMAIL_USER`: Your Gmail address
- `EMAIL_PASS`: Your Gmail app password
- `SECRET_KEY`: Auto-generated

### **3. Monthly Process (Manual)**
1. **On 1st of each month**: Log into admin panel
2. **Go to**: Fee Management
3. **Click**: "Assign Monthly Dues" button
4. **Confirm**: The action
5. **Done**: All students get their monthly dues

## 📊 **Monitoring and Troubleshooting**

### **Check if Dues are Assigned**
```bash
# Run the status check
python scripts/monthly_dues_manager.py
# Choose option 1: Show Current Status
```

### **Manual Assignment if Needed**
- **Admin Panel**: Fee Management → "Assign Monthly Dues" button
- **Script**: `python scripts/monthly_dues_manager.py` → Option 3

### **Common Issues**
1. **Dues not assigned**: Click the "Assign Monthly Dues" button
2. **Wrong amount**: Update monthly due amount in UPI settings
3. **Free tier limitations**: Remember no automatic scheduling

## 🎯 **Example Timeline (Free Tier)**

### **June 2025**
- **June 1st**: Admin logs in → Clicks "Assign Monthly Dues" → Existing students get June 2025 dues
- **June 15th**: New student joins → Gets June 2025 due immediately
- **June 30th**: All students have June 2025 dues

### **July 2025**
- **July 1st**: Admin logs in → Clicks "Assign Monthly Dues" → All students get July 2025 dues
- **July 10th**: Another new student joins → Gets July 2025 due immediately

## ✅ **Benefits of This System (Free Tier)**

1. **Simple**: One-click assignment from admin panel
2. **Fair**: Existing students pay monthly, new students pay for current month
3. **Flexible**: Can be triggered anytime
4. **Free**: Works within Render's free tier limitations
5. **Reliable**: Manual control ensures accuracy

## 🔄 **Manual Override Options**

### **Emergency Assignment**
- **Admin Panel**: Fee Management → "Assign Monthly Dues" button
- **Script**: `python scripts/monthly_dues_manager.py` → Option 3

### **Check Specific Student**
- **Admin Panel**: Fee Management (shows all students and their dues)

### **Individual Student Assignment**
- **Admin Panel**: Dues Management → Add due for specific student

## 💡 **Free Tier Tips**

1. **Set Reminder**: Mark your calendar for 1st of each month
2. **Check Regularly**: Visit Fee Management to monitor dues
3. **Use Scripts**: For bulk operations, use the Python scripts
4. **Monitor Logs**: Check Render logs for any errors

## 🚀 **Upgrade to Paid Tier (Optional)**

If you want automatic scheduling, consider upgrading to Render's paid tier which includes:
- ✅ **Cron Jobs**: Automatic monthly dues assignment
- ✅ **More Resources**: Better performance
- ✅ **24/7 Uptime**: No sleep mode

---

**The system works perfectly on free tier with manual triggers! Just remember to click the "Assign Monthly Dues" button on the 1st of each month.** 🎉 