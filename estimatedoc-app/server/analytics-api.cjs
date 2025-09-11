const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const { securityHeaders } = require('./middleware/security.cjs');

const app = express();
const PORT = process.env.ANALYTICS_PORT || 3001;

// Middleware
app.use(securityHeaders());
app.use(cors());
app.use(express.json({ limit: '10mb' }));

// Create analytics database
const dbPath = path.join(__dirname, 'analytics.db');
const db = new sqlite3.Database(dbPath);

// Initialize database schema
db.serialize(() => {
  // Sessions table
  db.run(`
    CREATE TABLE IF NOT EXISTS sessions (
      session_id TEXT PRIMARY KEY,
      visitor_id TEXT NOT NULL,
      start_time INTEGER NOT NULL,
      last_activity INTEGER NOT NULL,
      end_time INTEGER,
      page_views INTEGER DEFAULT 0,
      duration INTEGER DEFAULT 0,
      is_authenticated BOOLEAN DEFAULT 0,
      user_id TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);

  // Events table
  db.run(`
    CREATE TABLE IF NOT EXISTS events (
      event_id TEXT PRIMARY KEY,
      session_id TEXT NOT NULL,
      visitor_id TEXT NOT NULL,
      timestamp INTEGER NOT NULL,
      type TEXT NOT NULL,
      data TEXT,
      url TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    )
  `);

  // Page views table
  db.run(`
    CREATE TABLE IF NOT EXISTS page_views (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id TEXT NOT NULL,
      visitor_id TEXT NOT NULL,
      url TEXT NOT NULL,
      title TEXT,
      timestamp INTEGER NOT NULL,
      duration INTEGER DEFAULT 0,
      scroll_depth INTEGER DEFAULT 0,
      referrer TEXT,
      exit_type TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    )
  `);

  // Device info table
  db.run(`
    CREATE TABLE IF NOT EXISTS devices (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      visitor_id TEXT NOT NULL UNIQUE,
      type TEXT,
      browser_name TEXT,
      browser_version TEXT,
      os_name TEXT,
      os_version TEXT,
      screen_width INTEGER,
      screen_height INTEGER,
      cpu_cores INTEGER,
      memory INTEGER,
      platform TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);

  // Network info table
  db.run(`
    CREATE TABLE IF NOT EXISTS network_info (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id TEXT NOT NULL,
      type TEXT,
      downlink REAL,
      rtt INTEGER,
      effective_type TEXT,
      timestamp INTEGER NOT NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    )
  `);

  // Location info table
  db.run(`
    CREATE TABLE IF NOT EXISTS locations (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      visitor_id TEXT NOT NULL,
      country TEXT,
      region TEXT,
      city TEXT,
      timezone TEXT,
      language TEXT,
      ip_hash TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);

  // User actions table
  db.run(`
    CREATE TABLE IF NOT EXISTS user_actions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id TEXT NOT NULL,
      visitor_id TEXT NOT NULL,
      action_type TEXT NOT NULL,
      target TEXT,
      value TEXT,
      timestamp INTEGER NOT NULL,
      context TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    )
  `);

  // Performance metrics table
  db.run(`
    CREATE TABLE IF NOT EXISTS performance_metrics (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id TEXT NOT NULL,
      metric TEXT NOT NULL,
      value REAL NOT NULL,
      rating TEXT,
      timestamp INTEGER NOT NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    )
  `);

  // Error logs table
  db.run(`
    CREATE TABLE IF NOT EXISTS error_logs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id TEXT NOT NULL,
      message TEXT NOT NULL,
      stack TEXT,
      url TEXT,
      line INTEGER,
      column INTEGER,
      user_agent TEXT,
      timestamp INTEGER NOT NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    )
  `);

  // Create indexes for better query performance
  db.run(`CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id)`);
  db.run(`CREATE INDEX IF NOT EXISTS idx_events_visitor ON events(visitor_id)`);
  db.run(`CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)`);
  db.run(`CREATE INDEX IF NOT EXISTS idx_events_type ON events(type)`);
  db.run(`CREATE INDEX IF NOT EXISTS idx_sessions_visitor ON sessions(visitor_id)`);
  db.run(`CREATE INDEX IF NOT EXISTS idx_page_views_session ON page_views(session_id)`);
  db.run(`CREATE INDEX IF NOT EXISTS idx_user_actions_session ON user_actions(session_id)`);
});

// API Endpoints

// Batch event ingestion endpoint
app.post('/api/analytics/events', (req, res) => {
  const { events } = req.body;
  
  if (!events || !Array.isArray(events)) {
    return res.status(400).json({ error: 'Invalid events data' });
  }

  const errors = [];
  let processed = 0;

  db.serialize(() => {
    const stmt = db.prepare(`
      INSERT OR IGNORE INTO events (event_id, session_id, visitor_id, timestamp, type, data, url)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `);

    events.forEach(event => {
      try {
        // Process main event
        stmt.run(
          event.eventId,
          event.sessionId,
          event.visitorId,
          event.timestamp,
          event.type,
          JSON.stringify(event.data),
          event.data?.url || null,
          (err) => {
            if (err) errors.push({ eventId: event.eventId, error: err.message });
            else processed++;
          }
        );

        // Process specific event types
        processEventByType(event);
      } catch (err) {
        errors.push({ eventId: event.eventId, error: err.message });
      }
    });

    stmt.finalize();
  });

  // Return response after processing
  setTimeout(() => {
    res.json({
      success: true,
      processed,
      errors: errors.length > 0 ? errors : undefined
    });
  }, 100);
});

// Process specific event types
function processEventByType(event) {
  switch (event.type) {
    case 'pageview':
      if (event.data) {
        db.run(`
          INSERT OR REPLACE INTO page_views (
            session_id, visitor_id, url, title, timestamp, 
            duration, scroll_depth, referrer, exit_type
          ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        `, [
          event.sessionId,
          event.visitorId,
          event.data.url,
          event.data.title,
          event.timestamp,
          event.data.duration || 0,
          event.data.scrollDepth || 0,
          event.data.referrer,
          event.data.exitType
        ]);
      }
      break;

    case 'action':
      if (event.data) {
        db.run(`
          INSERT INTO user_actions (
            session_id, visitor_id, action_type, target, value, timestamp, context
          ) VALUES (?, ?, ?, ?, ?, ?, ?)
        `, [
          event.sessionId,
          event.visitorId,
          event.data.type,
          event.data.target,
          JSON.stringify(event.data.value),
          event.timestamp,
          JSON.stringify(event.data.context)
        ]);
      }
      break;

    case 'performance':
      if (event.data) {
        db.run(`
          INSERT INTO performance_metrics (
            session_id, metric, value, rating, timestamp
          ) VALUES (?, ?, ?, ?, ?)
        `, [
          event.sessionId,
          event.data.metric,
          event.data.value,
          event.data.rating,
          event.timestamp
        ]);
      }
      break;

    case 'error':
      if (event.data) {
        db.run(`
          INSERT INTO error_logs (
            session_id, message, stack, url, line, column, user_agent, timestamp
          ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        `, [
          event.sessionId,
          event.data.message,
          event.data.stack,
          event.data.url,
          event.data.line,
          event.data.column,
          event.data.userAgent,
          event.timestamp
        ]);
      }
      break;
  }

  // Store device info if present
  if (event.device) {
    db.run(`
      INSERT OR REPLACE INTO devices (
        visitor_id, type, browser_name, browser_version,
        os_name, os_version, screen_width, screen_height,
        cpu_cores, memory, platform
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `, [
      event.visitorId,
      event.device.type,
      event.device.browser.name,
      event.device.browser.version,
      event.device.os.name,
      event.device.os.version,
      event.device.screen.width,
      event.device.screen.height,
      event.device.hardware.cpuCores,
      event.device.hardware.memory,
      event.device.hardware.platform
    ]);
  }

  // Store network info if present
  if (event.network) {
    db.run(`
      INSERT INTO network_info (
        session_id, type, downlink, rtt, effective_type, timestamp
      ) VALUES (?, ?, ?, ?, ?, ?)
    `, [
      event.sessionId,
      event.network.type,
      event.network.downlink,
      event.network.rtt,
      event.network.effectiveType,
      event.timestamp
    ]);
  }

  // Store location info if present
  if (event.location) {
    db.run(`
      INSERT OR REPLACE INTO locations (
        visitor_id, country, region, city, timezone, language, ip_hash
      ) VALUES (?, ?, ?, ?, ?, ?, ?)
    `, [
      event.visitorId,
      event.location.country,
      event.location.region,
      event.location.city,
      event.location.timezone,
      event.location.language,
      event.location.ip
    ]);
  }
}

// Session management endpoint
app.post('/api/analytics/session', (req, res) => {
  const session = req.body;
  
  db.run(`
    INSERT OR REPLACE INTO sessions (
      session_id, visitor_id, start_time, last_activity,
      page_views, is_authenticated, user_id
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
  `, [
    session.sessionId,
    session.visitorId,
    session.startTime,
    session.lastActivity,
    session.pageViews || 0,
    session.isAuthenticated ? 1 : 0,
    session.userId
  ], (err) => {
    if (err) {
      res.status(500).json({ error: err.message });
    } else {
      res.json({ success: true });
    }
  });
});

// Analytics dashboard endpoints

// Get summary statistics
app.get('/api/analytics/stats', (req, res) => {
  const stats = {};

  db.serialize(() => {
    // Total sessions
    db.get(`SELECT COUNT(*) as total FROM sessions`, (err, row) => {
      stats.totalSessions = row?.total || 0;
    });

    // Unique visitors
    db.get(`SELECT COUNT(DISTINCT visitor_id) as total FROM sessions`, (err, row) => {
      stats.uniqueVisitors = row?.total || 0;
    });

    // Total page views
    db.get(`SELECT COUNT(*) as total FROM page_views`, (err, row) => {
      stats.totalPageViews = row?.total || 0;
    });

    // Total events
    db.get(`SELECT COUNT(*) as total FROM events`, (err, row) => {
      stats.totalEvents = row?.total || 0;
    });

    // Average session duration
    db.get(`
      SELECT AVG(last_activity - start_time) as avg_duration 
      FROM sessions 
      WHERE last_activity > start_time
    `, (err, row) => {
      stats.avgSessionDuration = Math.round(row?.avg_duration / 1000 / 60) || 0; // in minutes
    });

    // Top pages
    db.all(`
      SELECT url, title, COUNT(*) as views 
      FROM page_views 
      GROUP BY url 
      ORDER BY views DESC 
      LIMIT 10
    `, (err, rows) => {
      stats.topPages = rows || [];
    });

    // Browser distribution
    db.all(`
      SELECT browser_name, COUNT(*) as count 
      FROM devices 
      GROUP BY browser_name 
      ORDER BY count DESC
    `, (err, rows) => {
      stats.browsers = rows || [];
    });

    // Device types
    db.all(`
      SELECT type, COUNT(*) as count 
      FROM devices 
      GROUP BY type 
      ORDER BY count DESC
    `, (err, rows) => {
      stats.deviceTypes = rows || [];
    });

    // Recent errors
    db.all(`
      SELECT message, url, COUNT(*) as occurrences 
      FROM error_logs 
      GROUP BY message, url 
      ORDER BY id DESC 
      LIMIT 10
    `, (err, rows) => {
      stats.recentErrors = rows || [];
    });

    // Performance metrics
    db.all(`
      SELECT metric, AVG(value) as avg_value, 
             MIN(value) as min_value, 
             MAX(value) as max_value
      FROM performance_metrics 
      GROUP BY metric
    `, (err, rows) => {
      stats.performance = rows || [];
    });
  });

  // Send response after queries complete
  setTimeout(() => {
    res.json(stats);
  }, 200);
});

// Get recent events
app.get('/api/analytics/events', (req, res) => {
  const limit = parseInt(req.query.limit) || 100;
  const offset = parseInt(req.query.offset) || 0;
  const type = req.query.type;
  
  let query = `
    SELECT * FROM events 
    ${type ? 'WHERE type = ?' : ''}
    ORDER BY timestamp DESC 
    LIMIT ? OFFSET ?
  `;
  
  const params = type ? [type, limit, offset] : [limit, offset];
  
  db.all(query, params, (err, rows) => {
    if (err) {
      res.status(500).json({ error: err.message });
    } else {
      // Parse JSON data fields
      rows.forEach(row => {
        try {
          row.data = JSON.parse(row.data);
        } catch (e) {
          // Keep as string if not valid JSON
        }
      });
      res.json(rows);
    }
  });
});

// Get visitor timeline
app.get('/api/analytics/visitor/:visitorId', (req, res) => {
  const { visitorId } = req.params;
  
  const result = {
    visitor: {},
    sessions: [],
    events: [],
    pageViews: [],
    actions: []
  };

  db.serialize(() => {
    // Get visitor device info
    db.get(`SELECT * FROM devices WHERE visitor_id = ?`, [visitorId], (err, row) => {
      result.visitor.device = row;
    });

    // Get visitor location
    db.get(`SELECT * FROM locations WHERE visitor_id = ?`, [visitorId], (err, row) => {
      result.visitor.location = row;
    });

    // Get sessions
    db.all(`
      SELECT * FROM sessions 
      WHERE visitor_id = ? 
      ORDER BY start_time DESC
    `, [visitorId], (err, rows) => {
      result.sessions = rows || [];
    });

    // Get events
    db.all(`
      SELECT * FROM events 
      WHERE visitor_id = ? 
      ORDER BY timestamp DESC 
      LIMIT 100
    `, [visitorId], (err, rows) => {
      result.events = rows || [];
    });

    // Get page views
    db.all(`
      SELECT * FROM page_views 
      WHERE visitor_id = ? 
      ORDER BY timestamp DESC
    `, [visitorId], (err, rows) => {
      result.pageViews = rows || [];
    });

    // Get actions
    db.all(`
      SELECT * FROM user_actions 
      WHERE visitor_id = ? 
      ORDER BY timestamp DESC
    `, [visitorId], (err, rows) => {
      result.actions = rows || [];
    });
  });

  setTimeout(() => {
    res.json(result);
  }, 200);
});

// Real-time dashboard endpoint (SSE)
app.get('/api/analytics/realtime', (req, res) => {
  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive'
  });

  // Send current stats immediately
  const sendStats = () => {
    db.all(`
      SELECT * FROM events 
      ORDER BY timestamp DESC 
      LIMIT 10
    `, (err, rows) => {
      if (!err) {
        res.write(`data: ${JSON.stringify({ type: 'events', data: rows })}\n\n`);
      }
    });

    db.get(`
      SELECT COUNT(*) as active FROM sessions 
      WHERE last_activity > ?
    `, [Date.now() - 300000], (err, row) => { // Active in last 5 minutes
      if (!err) {
        res.write(`data: ${JSON.stringify({ type: 'activeSessions', count: row.active })}\n\n`);
      }
    });
  };

  // Send initial stats
  sendStats();

  // Send updates every 5 seconds
  const interval = setInterval(sendStats, 5000);

  // Clean up on client disconnect
  req.on('close', () => {
    clearInterval(interval);
  });
});

// Data retention cleanup (run daily)
function cleanupOldData() {
  const retentionDays = 90;
  const cutoffTime = Date.now() - (retentionDays * 24 * 60 * 60 * 1000);
  
  db.serialize(() => {
    // Delete old events
    db.run(`DELETE FROM events WHERE timestamp < ?`, [cutoffTime]);
    db.run(`DELETE FROM page_views WHERE timestamp < ?`, [cutoffTime]);
    db.run(`DELETE FROM user_actions WHERE timestamp < ?`, [cutoffTime]);
    db.run(`DELETE FROM performance_metrics WHERE timestamp < ?`, [cutoffTime]);
    db.run(`DELETE FROM error_logs WHERE timestamp < ?`, [cutoffTime]);
    
    // Delete old sessions
    db.run(`DELETE FROM sessions WHERE start_time < ?`, [cutoffTime]);
    
    // Vacuum to reclaim space
    db.run(`VACUUM`);
  });
  
  console.log('Cleaned up analytics data older than', retentionDays, 'days');
}

// Schedule cleanup daily
setInterval(cleanupOldData, 24 * 60 * 60 * 1000);

// Start server
app.listen(PORT, () => {
  console.log(`Analytics API server running on port ${PORT}`);
  console.log(`Database location: ${dbPath}`);
});