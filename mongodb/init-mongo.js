// MongoDB initialization script for Accessibility Scanner
db = db.getSiblingDB('accessibility_scanner');

// Create collections with proper indexes
db.createCollection('scan_requests');

// Create indexes for performance
db.scan_requests.createIndex({ "id": 1 }, { unique: true });
db.scan_requests.createIndex({ "user_id": 1 });
db.scan_requests.createIndex({ "createdAt": -1 });
db.scan_requests.createIndex({ "status": 1 });
db.scan_requests.createIndex({ "tool": 1 });

print('Database initialized with indexes for accessibility scanner');