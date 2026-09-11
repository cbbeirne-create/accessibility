// MongoDB initialization script for Auditly
db = db.getSiblingDB('accessibility_scanner');

const collections = [
  'users',
  'scan_requests',
  'scan_jobs',
  'refresh_tokens',
  'rate_limits',
  'scheduled_scans',
  'notifications',
  'organizations',
  'organization_members',
  'organization_invites',
  'stripe_events'
];

collections.forEach((name) => {
  if (!db.getCollectionNames().includes(name)) db.createCollection(name);
});

db.users.createIndex({ id: 1 }, { unique: true });
db.users.createIndex({ email: 1 }, { unique: true });
db.users.createIndex({ stripe_customer_id: 1 }, { sparse: true });

db.scan_requests.createIndex({ id: 1 }, { unique: true });
db.scan_requests.createIndex({ user_id: 1, createdAt: -1 });
db.scan_requests.createIndex({ organization_id: 1, createdAt: -1 });
db.scan_requests.createIndex({ status: 1, createdAt: -1 });

db.scan_jobs.createIndex({ id: 1 }, { unique: true });
db.scan_jobs.createIndex({ scan_id: 1 });
db.scan_jobs.createIndex({ status: 1, available_at: 1 });
db.scan_jobs.createIndex({ lock_until: 1 });

db.refresh_tokens.createIndex({ token_hash: 1 }, { unique: true });
db.refresh_tokens.createIndex({ user_id: 1, revoked_at: 1 });
db.refresh_tokens.createIndex({ expires_at: 1 }, { expireAfterSeconds: 0 });

db.rate_limits.createIndex({ key: 1, bucket_start: 1 }, { unique: true });
db.rate_limits.createIndex({ expires_at: 1 }, { expireAfterSeconds: 0 });

db.scheduled_scans.createIndex({ id: 1 }, { unique: true });
db.scheduled_scans.createIndex({ user_id: 1, created_at: -1 });
db.scheduled_scans.createIndex({ enabled: 1, next_run: 1, lock_until: 1 });

db.notifications.createIndex({ user_id: 1, created_at: -1 });
db.notifications.createIndex({ event_key: 1 }, { unique: true, sparse: true });

db.organizations.createIndex({ id: 1 }, { unique: true });
db.organization_members.createIndex({ organization_id: 1, user_id: 1 }, { unique: true });
db.organization_invites.createIndex({ token: 1 }, { unique: true });
db.organization_invites.createIndex({ email: 1, expires_at: 1 });

db.stripe_events.createIndex({ event_id: 1 }, { unique: true });

print('Auditly database initialized with security and queue indexes');
