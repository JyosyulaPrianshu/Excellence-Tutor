# Excellence Tutorial - Entity Relationship Diagram (ERD)

## 🎨 **Visual Database Schema**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     USERS       │    │    PROFILES     │    │     TESTS       │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ id (PK)         │◄──►│ id (PK)         │    │ id (PK)         │
│ email (UNIQUE)  │    │ user_id (FK)    │    │ name            │
│ password        │    │ full_name       │    │ date            │
│ is_admin        │    │ parent_name     │    │ total_marks     │
│ created_at      │    │ parent_phone    │    │ class_for       │
└─────────────────┘    │ student_phone   │    │ question_paper  │
                       │ student_class   │    └─────────────────┘
                       │ school_name     │              │
                       │ roll_number     │              │
                       │ profile_pic     │              │
                       │ last_seen_*     │              │
                       │ pending_popup   │              │
                       └─────────────────┘              │
                                │                       │
                                │                       │
                                ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│      FEES       │    │     MARKS       │◄───┤                 │
├─────────────────┤    ├─────────────────┤    │                 │
│ id (PK)         │    │ id (PK)         │    │                 │
│ user_id (FK)    │◄───┤ user_id (FK)    │    │                 │
│ month           │    │ test_id (FK)    │────┘                 │
│ amount_due      │    │ marks_obtained  │                      │
│ is_paid         │    │ updated_at      │                      │
└─────────────────┘    └─────────────────┘                      │
         │                                                      │
         │                                                      │
         ▼                                                      │
┌─────────────────┐                                            │
│    PAYMENTS     │                                            │
├─────────────────┤                                            │
│ id (PK)         │                                            │
│ user_id (FK)    │◄───────────────────────────────────────────┘
│ fee_id (FK)     │
│ method          │
│ reference       │
│ is_confirmed    │
│ requested_at    │
│ confirmed_at    │
└─────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ NOTIFICATIONS   │    │      PDFS       │    │   RESOURCES     │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ id (PK)         │    │ id (PK)         │    │ id (PK)         │
│ user_id (FK)    │◄───┤ title           │    │ name            │
│ message         │    │ file_path       │    │ link            │
│ class_for       │    │ cloudinary_url  │    │ description     │
│ seen            │    │ class_for       │    │ class_for       │
│ created_at      │    │ uploaded_at     │    │ created_by (FK) │◄──┐
└─────────────────┘    └─────────────────┘    │ created_at      │   │
                                              └─────────────────┘   │
                                                                    │
┌─────────────────┐    ┌─────────────────┐                        │
│    SETTINGS     │    │ DROPOUT_REQUESTS│                        │
├─────────────────┤    ├─────────────────┤                        │
│ id (PK)         │    │ id (PK)         │                        │
│ key (UNIQUE)    │    │ user_id (FK)    │◄───────────────────────┘
│ value           │    │ status          │
└─────────────────┘    │ admin_response  │
                       │ requested_at    │
                       │ processed_at    │
                       └─────────────────┘
```

## 🔗 **Relationship Details**

### **Core Relationships:**
- **Users ↔ Profiles**: 1:1 (Each user has one profile)
- **Users ↔ Marks**: 1:N (Student can have multiple test marks)
- **Users ↔ Fees**: 1:N (Student can have multiple monthly fees)
- **Users ↔ Payments**: 1:N (Student can make multiple payments)
- **Tests ↔ Marks**: 1:N (Each test can have multiple student marks)
- **Fees ↔ Payments**: 1:N (Each fee can have multiple payment attempts)

### **Content Relationships:**
- **Users ↔ Notifications**: 1:N (Personal notifications)
- **Users ↔ Resources**: 1:N (Created by relationship)
- **Users ↔ Dropout Requests**: 1:N (Student dropout requests)

### **Class-Based Content:**
- **PDFs**: Filtered by `class_for` field
- **Tests**: Filtered by `class_for` field  
- **Notifications**: Filtered by `class_for` field
- **Resources**: Filtered by `class_for` field

## 📊 **Data Flow Patterns**

### **Student Registration Flow:**
```
1. User creates account (users table)
2. Profile information added (profiles table)
3. Roll number assigned (unique per class)
4. Student can access class-specific content
```

### **Fee Management Flow:**
```
1. Admin assigns monthly fees (fees table)
2. Student makes payment (payments table)
3. Admin approves payment (is_confirmed = true)
4. Fee marked as paid (is_paid = true)
```

### **Test Management Flow:**
```
1. Admin creates test (tests table)
2. Student submits marks (marks table)
3. Marks validated and stored
4. Leaderboard calculated from marks
```

### **Content Delivery Flow:**
```
1. Admin uploads content (pdfs/resources tables)
2. Content filtered by student class
3. Student accesses relevant content
4. Last seen tracking updated (profiles table)
```

## 🎯 **Key Design Decisions**

### **1. Class-Based Architecture:**
- Single `class_for` field enables multi-class content
- Supports 9 different class/stream combinations
- "all" value for universal content

### **2. Flexible Notification System:**
- Personal notifications (user_id set)
- Class notifications (user_id null, class_for set)
- Universal notifications (user_id null, class_for = 'all')

### **3. Payment Tracking:**
- Separate payments table for audit trail
- Multiple payment attempts per fee allowed
- UPI reference tracking for verification

### **4. Roll Number System:**
- Unique per class (not globally unique)
- Allows same roll numbers across different classes
- Constraint: `UNIQUE(student_class, roll_number)`

### **5. File Storage Strategy:**
- Local file storage (file_path)
- Cloud storage backup (cloudinary_url)
- Graceful fallback between storage methods

This ERD represents a mature educational management system with comprehensive student lifecycle management, flexible content delivery, and robust payment tracking! 🎓