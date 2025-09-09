# EstimateDoc Database & UI Implementation Strategy

## Executive Summary

This document provides a comprehensive implementation strategy for importing EstimateDoc data into PostgreSQL and building an interactive UI for visualization and effort calculation.

---

## Part 1: Database Implementation

### 1.1 PostgreSQL Schema Design

```sql
-- Create database
CREATE DATABASE estimatedoc;

-- Main schema
CREATE SCHEMA IF NOT EXISTS templates;

-- Core Tables
CREATE TABLE templates.documents (
    document_id SERIAL PRIMARY KEY,
    client_req_title VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    original_complexity VARCHAR(50),
    calculated_complexity VARCHAR(50),
    complexity_score DECIMAL(10,2),
    manifest_code VARCHAR(100),
    manifest_name VARCHAR(255),
    prec_title VARCHAR(255),
    prec_desc TEXT,
    sql_document_id INTEGER,
    sql_filename VARCHAR(255),
    total_fields INTEGER DEFAULT 0,
    match_status VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE templates.field_categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) UNIQUE NOT NULL,
    category_description TEXT,
    base_effort_hours DECIMAL(5,2) DEFAULT 1.0,
    is_reusable BOOLEAN DEFAULT FALSE
);

CREATE TABLE templates.fields (
    field_id SERIAL PRIMARY KEY,
    field_code TEXT,
    field_result TEXT,
    category_id INTEGER REFERENCES templates.field_categories(category_id),
    usage_count INTEGER DEFAULT 1,
    is_unique BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE templates.document_fields (
    document_id INTEGER REFERENCES templates.documents(document_id),
    field_id INTEGER REFERENCES templates.fields(field_id),
    instance_count INTEGER DEFAULT 1,
    is_unique_to_doc BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (document_id, field_id)
);

CREATE TABLE templates.complexity_config (
    config_id SERIAL PRIMARY KEY,
    parameter_name VARCHAR(100) UNIQUE NOT NULL,
    parameter_value DECIMAL(10,2),
    parameter_type VARCHAR(50), -- 'threshold' or 'weight'
    description TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE templates.effort_calculations (
    calculation_id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES templates.documents(document_id),
    total_hours DECIMAL(10,2),
    unique_field_hours DECIMAL(10,2),
    common_field_hours DECIMAL(10,2),
    saved_hours DECIMAL(10,2),
    calculation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    config_snapshot JSONB, -- Store config used for this calculation
    user_id INTEGER,
    notes TEXT
);

-- Indexes for performance
CREATE INDEX idx_documents_complexity ON templates.documents(calculated_complexity);
CREATE INDEX idx_documents_title ON templates.documents(client_req_title);
CREATE INDEX idx_fields_category ON templates.fields(category_id);
CREATE INDEX idx_document_fields_doc ON templates.document_fields(document_id);
CREATE INDEX idx_effort_calc_date ON templates.effort_calculations(calculation_date);

-- Views for reporting
CREATE VIEW templates.document_summary AS
SELECT 
    d.document_id,
    d.client_req_title,
    d.description,
    d.calculated_complexity,
    d.complexity_score,
    COUNT(DISTINCT df.field_id) as field_count,
    COUNT(DISTINCT CASE WHEN f.is_unique THEN f.field_id END) as unique_fields,
    COUNT(DISTINCT CASE WHEN NOT f.is_unique THEN f.field_id END) as common_fields
FROM templates.documents d
LEFT JOIN templates.document_fields df ON d.document_id = df.document_id
LEFT JOIN templates.fields f ON df.field_id = f.field_id
GROUP BY d.document_id;

CREATE VIEW templates.field_usage_stats AS
SELECT 
    fc.category_name,
    COUNT(f.field_id) as total_fields,
    SUM(f.usage_count) as total_usage,
    AVG(f.usage_count) as avg_usage,
    COUNT(CASE WHEN f.is_unique THEN 1 END) as unique_count,
    COUNT(CASE WHEN NOT f.is_unique THEN 1 END) as common_count
FROM templates.fields f
JOIN templates.field_categories fc ON f.category_id = fc.category_id
GROUP BY fc.category_name;
```

### 1.2 Data Import Scripts

```python
# import_to_postgres.py
import json
import psycopg2
from psycopg2.extras import execute_batch
import pandas as pd
from datetime import datetime

# Database connection
conn = psycopg2.connect(
    host="localhost",
    database="estimatedoc",
    user="your_user",
    password="your_password"
)
cur = conn.cursor()

# Load data
with open('ClaudeExecution/EstimateDoc_Export.json', 'r') as f:
    data = json.load(f)

# Insert field categories
categories = [
    ('IF Statements', 'Conditional logic statements', 3.0, False),
    ('Document Variables', 'Document-level variables', 2.0, False),
    ('Merge Fields', 'Mail merge fields', 1.5, False),
    ('Precedent Scripts', 'Embedded scripts', 4.0, False),
    ('Include Text', 'Text inclusion references', 1.0, True),
    ('References', 'Cross-references', 0.5, True),
    ('Other Fields', 'Uncategorized fields', 1.0, False)
]

for cat in categories:
    cur.execute("""
        INSERT INTO templates.field_categories 
        (category_name, category_description, base_effort_hours, is_reusable)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (category_name) DO UPDATE
        SET base_effort_hours = EXCLUDED.base_effort_hours
    """, cat)

# Insert documents
for template in data['templates']:
    cur.execute("""
        INSERT INTO templates.documents (
            client_req_title, description, original_complexity,
            calculated_complexity, complexity_score, manifest_code,
            manifest_name, prec_title, sql_document_id, sql_filename,
            total_fields, match_status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (client_req_title) DO UPDATE
        SET 
            calculated_complexity = EXCLUDED.calculated_complexity,
            complexity_score = EXCLUDED.complexity_score,
            updated_at = CURRENT_TIMESTAMP
    """, (
        template.get('ClientReq_Title'),
        template.get('ClientReq_Description'),
        template.get('Original Complexity'),
        template.get('Calculated Complexity'),
        template.get('Complexity Score', 0),
        template.get('Manifest_Code'),
        template.get('Manifest_Name'),
        template.get('Subfolder_PrecTitle'),
        template.get('SQL_DocumentID'),
        template.get('SQL_Filename'),
        template.get('Total Fields', 0),
        template.get('Match_Status')
    ))

# Insert complexity configuration
config_items = [
    ('simple_threshold', 10, 'threshold', 'Templates below this score are Simple'),
    ('moderate_threshold', 30, 'threshold', 'Templates below this score are Moderate'),
    ('total_fields_weight', 1.0, 'weight', 'Multiplier for total field count'),
    ('unique_if_weight', 3.0, 'weight', 'Multiplier for unique IF statements'),
    ('unique_var_weight', 2.0, 'weight', 'Multiplier for unique variables'),
    ('unique_script_weight', 4.0, 'weight', 'Multiplier for unique scripts'),
    ('common_if_weight', 0.5, 'weight', 'Multiplier for common IF statements'),
    ('common_var_weight', 0.3, 'weight', 'Multiplier for common variables')
]

for config in config_items:
    cur.execute("""
        INSERT INTO templates.complexity_config 
        (parameter_name, parameter_value, parameter_type, description)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (parameter_name) DO UPDATE
        SET parameter_value = EXCLUDED.parameter_value,
            updated_at = CURRENT_TIMESTAMP
    """, config)

conn.commit()
print("Data import completed successfully!")
```

### 1.3 Database Functions and Procedures

```sql
-- Function to calculate complexity score
CREATE OR REPLACE FUNCTION templates.calculate_complexity_score(
    p_document_id INTEGER
) RETURNS DECIMAL AS $$
DECLARE
    v_score DECIMAL(10,2);
    v_config RECORD;
    v_field_counts RECORD;
BEGIN
    -- Get current configuration
    SELECT 
        MAX(CASE WHEN parameter_name = 'total_fields_weight' THEN parameter_value END) as total_weight,
        MAX(CASE WHEN parameter_name = 'unique_if_weight' THEN parameter_value END) as if_weight,
        MAX(CASE WHEN parameter_name = 'unique_var_weight' THEN parameter_value END) as var_weight,
        MAX(CASE WHEN parameter_name = 'common_if_weight' THEN parameter_value END) as common_if_weight
    INTO v_config
    FROM templates.complexity_config
    WHERE active = TRUE;
    
    -- Get field counts for document
    SELECT 
        COUNT(*) as total_fields,
        COUNT(CASE WHEN fc.category_name = 'IF Statements' AND f.is_unique THEN 1 END) as unique_if,
        COUNT(CASE WHEN fc.category_name = 'Document Variables' AND f.is_unique THEN 1 END) as unique_var,
        COUNT(CASE WHEN fc.category_name = 'IF Statements' AND NOT f.is_unique THEN 1 END) as common_if
    INTO v_field_counts
    FROM templates.document_fields df
    JOIN templates.fields f ON df.field_id = f.field_id
    JOIN templates.field_categories fc ON f.category_id = fc.category_id
    WHERE df.document_id = p_document_id;
    
    -- Calculate score
    v_score := 
        (v_field_counts.total_fields * v_config.total_weight) +
        (v_field_counts.unique_if * v_config.if_weight) +
        (v_field_counts.unique_var * v_config.var_weight) +
        (v_field_counts.common_if * v_config.common_if_weight);
    
    RETURN v_score;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update complexity on changes
CREATE OR REPLACE FUNCTION templates.update_complexity_trigger()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE templates.documents
    SET 
        complexity_score = templates.calculate_complexity_score(NEW.document_id),
        updated_at = CURRENT_TIMESTAMP
    WHERE document_id = NEW.document_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_complexity
AFTER INSERT OR UPDATE ON templates.document_fields
FOR EACH ROW
EXECUTE FUNCTION templates.update_complexity_trigger();
```

---

## Part 2: UI Implementation Strategy

### 2.1 Technology Stack

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: estimatedoc
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://admin:secure_password@postgres:5432/estimatedoc
      NODE_ENV: production
    ports:
      - "3001:3001"
    depends_on:
      - postgres

  frontend:
    build: ./frontend
    environment:
      REACT_APP_API_URL: http://localhost:3001
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_data:
```

### 2.2 Backend API (Node.js + Express)

```javascript
// backend/server.js
const express = require('express');
const { Pool } = require('pg');
const cors = require('cors');

const app = express();
const pool = new Pool({
  connectionString: process.env.DATABASE_URL
});

app.use(cors());
app.use(express.json());

// API Endpoints
app.get('/api/templates', async (req, res) => {
  const { complexity, search } = req.query;
  let query = 'SELECT * FROM templates.document_summary WHERE 1=1';
  const params = [];
  
  if (complexity) {
    params.push(complexity);
    query += ` AND calculated_complexity = $${params.length}`;
  }
  
  if (search) {
    params.push(`%${search}%`);
    query += ` AND (client_req_title ILIKE $${params.length} OR description ILIKE $${params.length})`;
  }
  
  const result = await pool.query(query, params);
  res.json(result.rows);
});

app.get('/api/templates/:id', async (req, res) => {
  const { id } = req.params;
  const template = await pool.query(
    'SELECT * FROM templates.documents WHERE document_id = $1',
    [id]
  );
  
  const fields = await pool.query(`
    SELECT fc.category_name, COUNT(*) as count, 
           SUM(CASE WHEN f.is_unique THEN 1 ELSE 0 END) as unique_count
    FROM templates.document_fields df
    JOIN templates.fields f ON df.field_id = f.field_id
    JOIN templates.field_categories fc ON f.category_id = fc.category_id
    WHERE df.document_id = $1
    GROUP BY fc.category_name
  `, [id]);
  
  res.json({
    template: template.rows[0],
    fields: fields.rows
  });
});

app.post('/api/calculate-effort', async (req, res) => {
  const { templateIds, config } = req.body;
  
  // Calculate effort based on provided config
  const calculations = [];
  
  for (const id of templateIds) {
    const fields = await pool.query(`
      SELECT fc.category_name, fc.base_effort_hours,
             COUNT(*) as count,
             SUM(CASE WHEN f.is_unique THEN 1 ELSE 0 END) as unique_count
      FROM templates.document_fields df
      JOIN templates.fields f ON df.field_id = f.field_id
      JOIN templates.field_categories fc ON f.category_id = fc.category_id
      WHERE df.document_id = $1
      GROUP BY fc.category_name, fc.base_effort_hours
    `, [id]);
    
    let totalHours = 0;
    let uniqueHours = 0;
    let commonHours = 0;
    
    fields.rows.forEach(row => {
      const uniqueEffort = row.unique_count * row.base_effort_hours * (config[row.category_name] || 1);
      const commonEffort = (row.count - row.unique_count) * row.base_effort_hours * 0.1;
      
      uniqueHours += uniqueEffort;
      commonHours += commonEffort;
      totalHours += uniqueEffort + commonEffort;
    });
    
    calculations.push({
      templateId: id,
      totalHours,
      uniqueHours,
      commonHours,
      savedHours: commonHours * 0.9
    });
    
    // Save calculation to database
    await pool.query(`
      INSERT INTO templates.effort_calculations 
      (document_id, total_hours, unique_field_hours, common_field_hours, saved_hours, config_snapshot)
      VALUES ($1, $2, $3, $4, $5, $6)
    `, [id, totalHours, uniqueHours, commonHours, commonHours * 0.9, JSON.stringify(config)]);
  }
  
  res.json(calculations);
});

app.get('/api/statistics', async (req, res) => {
  const complexity = await pool.query(`
    SELECT calculated_complexity, COUNT(*) as count
    FROM templates.documents
    GROUP BY calculated_complexity
  `);
  
  const fields = await pool.query('SELECT * FROM templates.field_usage_stats');
  
  const recent = await pool.query(`
    SELECT * FROM templates.effort_calculations
    ORDER BY calculation_date DESC
    LIMIT 10
  `);
  
  res.json({
    complexityDistribution: complexity.rows,
    fieldStatistics: fields.rows,
    recentCalculations: recent.rows
  });
});

app.listen(3001, () => {
  console.log('API server running on port 3001');
});
```

### 2.3 Frontend React Application

```jsx
// frontend/src/App.js
import React, { useState, useEffect } from 'react';
import {
  Container, Grid, Paper, Typography, 
  TextField, Select, MenuItem, Button,
  Table, TableBody, TableCell, TableHead, TableRow,
  Card, CardContent
} from '@mui/material';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';

function App() {
  const [templates, setTemplates] = useState([]);
  const [selectedTemplates, setSelectedTemplates] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [effortConfig, setEffortConfig] = useState({
    'IF Statements': 3.0,
    'Document Variables': 2.0,
    'Merge Fields': 1.5,
    'Precedent Scripts': 4.0
  });

  useEffect(() => {
    fetchTemplates();
    fetchStatistics();
  }, []);

  const fetchTemplates = async (filters = {}) => {
    const params = new URLSearchParams(filters);
    const response = await fetch(`http://localhost:3001/api/templates?${params}`);
    const data = await response.json();
    setTemplates(data);
  };

  const fetchStatistics = async () => {
    const response = await fetch('http://localhost:3001/api/statistics');
    const data = await response.json();
    setStatistics(data);
  };

  const calculateEffort = async () => {
    const response = await fetch('http://localhost:3001/api/calculate-effort', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        templateIds: selectedTemplates,
        config: effortConfig
      })
    });
    const calculations = await response.json();
    displayResults(calculations);
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4 }}>
      <Typography variant="h3" gutterBottom>
        EstimateDoc Template Analysis
      </Typography>

      <Grid container spacing={3}>
        {/* Statistics Dashboard */}
        <Grid item xs={12} md={4}>
          <Paper elevation={3} sx={{ p: 2 }}>
            <Typography variant="h6">Complexity Distribution</Typography>
            {statistics && (
              <PieChart width={300} height={200}>
                <Pie
                  data={statistics.complexityDistribution}
                  dataKey="count"
                  nameKey="calculated_complexity"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                >
                  <Cell fill="#4caf50" />
                  <Cell fill="#ff9800" />
                  <Cell fill="#f44336" />
                </Pie>
                <Tooltip />
              </PieChart>
            )}
          </Paper>
        </Grid>

        {/* Field Statistics */}
        <Grid item xs={12} md={8}>
          <Paper elevation={3} sx={{ p: 2 }}>
            <Typography variant="h6">Field Category Distribution</Typography>
            {statistics && (
              <BarChart width={600} height={200} data={statistics.fieldStatistics}>
                <XAxis dataKey="category_name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="total_fields" fill="#2196f3" />
              </BarChart>
            )}
          </Paper>
        </Grid>

        {/* Template Search and Filter */}
        <Grid item xs={12}>
          <Paper elevation={3} sx={{ p: 2 }}>
            <Typography variant="h6">Template Search</Typography>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  label="Search Templates"
                  onChange={(e) => fetchTemplates({ search: e.target.value })}
                />
              </Grid>
              <Grid item xs={3}>
                <Select
                  fullWidth
                  label="Complexity"
                  onChange={(e) => fetchTemplates({ complexity: e.target.value })}
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="Simple">Simple</MenuItem>
                  <MenuItem value="Moderate">Moderate</MenuItem>
                  <MenuItem value="Complex">Complex</MenuItem>
                </Select>
              </Grid>
              <Grid item xs={3}>
                <Button 
                  variant="contained" 
                  fullWidth
                  onClick={calculateEffort}
                  disabled={selectedTemplates.length === 0}
                >
                  Calculate Effort
                </Button>
              </Grid>
            </Grid>

            {/* Template Table */}
            <Table sx={{ mt: 2 }}>
              <TableHead>
                <TableRow>
                  <TableCell>Select</TableCell>
                  <TableCell>Template Title</TableCell>
                  <TableCell>Description</TableCell>
                  <TableCell>Complexity</TableCell>
                  <TableCell>Fields</TableCell>
                  <TableCell>Score</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {templates.map((template) => (
                  <TableRow key={template.document_id}>
                    <TableCell>
                      <input
                        type="checkbox"
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedTemplates([...selectedTemplates, template.document_id]);
                          } else {
                            setSelectedTemplates(selectedTemplates.filter(id => id !== template.document_id));
                          }
                        }}
                      />
                    </TableCell>
                    <TableCell>{template.client_req_title}</TableCell>
                    <TableCell>{template.description}</TableCell>
                    <TableCell>{template.calculated_complexity}</TableCell>
                    <TableCell>{template.field_count}</TableCell>
                    <TableCell>{template.complexity_score}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Paper>
        </Grid>

        {/* Effort Calculator Configuration */}
        <Grid item xs={12}>
          <Paper elevation={3} sx={{ p: 2 }}>
            <Typography variant="h6">Effort Calculation Configuration</Typography>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              {Object.entries(effortConfig).map(([category, hours]) => (
                <Grid item xs={3} key={category}>
                  <TextField
                    fullWidth
                    label={category}
                    type="number"
                    value={hours}
                    onChange={(e) => setEffortConfig({
                      ...effortConfig,
                      [category]: parseFloat(e.target.value)
                    })}
                    InputProps={{ inputProps: { min: 0, step: 0.5 } }}
                  />
                </Grid>
              ))}
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
}

export default App;
```

### 2.4 Deployment Configuration

```nginx
# nginx.conf
server {
    listen 80;
    server_name estimatedoc.example.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
    }
}
```

---

## Part 3: Effort Calculation Features

### 3.1 Interactive Calculator Components

```jsx
// frontend/src/components/EffortCalculator.js
import React, { useState } from 'react';
import {
  Dialog, DialogTitle, DialogContent,
  Table, TableBody, TableCell, TableHead, TableRow,
  Typography, Chip, Box
} from '@mui/material';

function EffortCalculator({ calculations, open, onClose }) {
  const totalEffort = calculations.reduce((sum, calc) => sum + calc.totalHours, 0);
  const totalSaved = calculations.reduce((sum, calc) => sum + calc.savedHours, 0);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Effort Calculation Results</DialogTitle>
      <DialogContent>
        <Box sx={{ mb: 2 }}>
          <Typography variant="h6">
            Total Effort: {totalEffort.toFixed(2)} hours
          </Typography>
          <Typography color="success.main">
            Saved through reuse: {totalSaved.toFixed(2)} hours
          </Typography>
        </Box>

        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Template</TableCell>
              <TableCell align="right">Unique Fields (hrs)</TableCell>
              <TableCell align="right">Common Fields (hrs)</TableCell>
              <TableCell align="right">Total (hrs)</TableCell>
              <TableCell align="right">Saved (hrs)</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {calculations.map((calc) => (
              <TableRow key={calc.templateId}>
                <TableCell>{calc.templateId}</TableCell>
                <TableCell align="right">{calc.uniqueHours.toFixed(2)}</TableCell>
                <TableCell align="right">{calc.commonHours.toFixed(2)}</TableCell>
                <TableCell align="right">
                  <Chip 
                    label={`${calc.totalHours.toFixed(2)} hrs`}
                    color="primary"
                  />
                </TableCell>
                <TableCell align="right">
                  <Chip 
                    label={`${calc.savedHours.toFixed(2)} hrs`}
                    color="success"
                  />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </DialogContent>
    </Dialog>
  );
}

export default EffortCalculator;
```

### 3.2 Batch Processing

```javascript
// backend/batchProcessor.js
const processBatch = async (templateIds) => {
  const batchSize = 50;
  const results = [];
  
  for (let i = 0; i < templateIds.length; i += batchSize) {
    const batch = templateIds.slice(i, i + batchSize);
    const batchResults = await Promise.all(
      batch.map(id => calculateTemplateEffort(id))
    );
    results.push(...batchResults);
    
    // Update progress
    const progress = Math.min(100, ((i + batchSize) / templateIds.length) * 100);
    await updateProgress(progress);
  }
  
  return results;
};
```

---

## Part 4: Performance Optimization

### 4.1 Caching Strategy

```javascript
// backend/cache.js
const Redis = require('redis');
const client = Redis.createClient();

const cacheMiddleware = (duration = 300) => {
  return async (req, res, next) => {
    const key = `cache:${req.originalUrl}`;
    
    try {
      const cached = await client.get(key);
      if (cached) {
        return res.json(JSON.parse(cached));
      }
    } catch (err) {
      console.error('Cache error:', err);
    }
    
    res.sendResponse = res.json;
    res.json = (body) => {
      client.setex(key, duration, JSON.stringify(body));
      res.sendResponse(body);
    };
    
    next();
  };
};
```

### 4.2 Database Optimization

```sql
-- Materialized view for performance
CREATE MATERIALIZED VIEW templates.template_effort_summary AS
SELECT 
    d.document_id,
    d.client_req_title,
    d.calculated_complexity,
    COUNT(DISTINCT df.field_id) as total_fields,
    SUM(CASE WHEN fc.category_name = 'IF Statements' THEN 1 ELSE 0 END) as if_count,
    SUM(CASE WHEN fc.category_name = 'Document Variables' THEN 1 ELSE 0 END) as var_count,
    SUM(CASE WHEN f.is_unique THEN fc.base_effort_hours ELSE fc.base_effort_hours * 0.1 END) as estimated_hours
FROM templates.documents d
LEFT JOIN templates.document_fields df ON d.document_id = df.document_id
LEFT JOIN templates.fields f ON df.field_id = f.field_id
LEFT JOIN templates.field_categories fc ON f.category_id = fc.category_id
GROUP BY d.document_id;

-- Refresh strategy
CREATE OR REPLACE FUNCTION templates.refresh_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY templates.template_effort_summary;
END;
$$ LANGUAGE plpgsql;

-- Schedule refresh (using pg_cron)
SELECT cron.schedule('refresh-views', '0 * * * *', 
  'SELECT templates.refresh_materialized_views()');
```

---

## Implementation Timeline

### Phase 1: Database Setup (Week 1)
- [ ] Set up PostgreSQL instance
- [ ] Create schema and tables
- [ ] Import initial data
- [ ] Test queries and functions

### Phase 2: Backend Development (Week 2)
- [ ] Set up Node.js project
- [ ] Implement API endpoints
- [ ] Add authentication
- [ ] Test API functionality

### Phase 3: Frontend Development (Weeks 3-4)
- [ ] Create React application
- [ ] Build UI components
- [ ] Integrate with API
- [ ] Add visualizations

### Phase 4: Testing & Deployment (Week 5)
- [ ] Unit and integration testing
- [ ] Performance testing
- [ ] Deploy to staging
- [ ] User acceptance testing

### Phase 5: Production Release (Week 6)
- [ ] Production deployment
- [ ] Monitoring setup
- [ ] Documentation
- [ ] Training materials

---

*Implementation Guide Version: 1.0*
*Last Updated: 2025-09-09*