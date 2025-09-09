# EstimateDoc Analytics Dashboard

A comprehensive TypeScript-based web application for visualizing and analyzing EstimateDoc data with real-time charts and interactive tables.

## 🎯 Features

- **Real-time Statistics**: Live overview of documents, fields, templates, and matching rates
- **Interactive Charts**: 
  - Complexity distribution bar chart
  - Matching confidence doughnut chart
  - Field reusability horizontal bar chart
  - Complexity trends line chart
- **Detailed Template Table**: Paginated view of all templates with complexity and matching status
- **Responsive Design**: Works on desktop and mobile devices
- **TypeScript Backend**: Type-safe Express.js API server
- **PostgreSQL Integration**: Direct connection to EstimateDoc database

## 🚀 Quick Start

### React Application

```bash
# Install dependencies
cd client
npm install

# Start the React app
npm start
```

## 📊 Dashboard Overview

### Key Metrics Displayed:
- **Total Documents**: 782 imported documents
- **Total Fields**: 11,653 unique fields
- **Match Rate**: 98.9% template matching success
- **Templates**: 1,082 of 1,094 matched

### Data Visualizations:

1. **Complexity Distribution**: Shows the breakdown of templates by complexity level (Simple, Moderate, Complex)
2. **Matching Confidence**: Pie chart showing High/Medium/Low confidence matches
3. **Field Reusability**: Analysis of field usage across documents
4. **Complexity Trends**: Average metrics (fields, IF statements, scripts) by complexity level

## 🛠️ Technology Stack

- **Frontend**: 
  - TypeScript/React for component-based UI
  - Chart.js for data visualization
  - Tailwind CSS for styling (standalone version uses inline styles)
  
- **Backend**:
  - Node.js/Express with TypeScript
  - PostgreSQL database
  - RESTful API architecture

## 📁 Project Structure

```
estimatedoc-dashboard/
├── server/                 # Express backend
│   ├── src/
│   │   └── index.ts       # API endpoints
│   ├── package.json
│   └── tsconfig.json
├── client/                 # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── services/      # API service layer
│   │   └── App.tsx        # Main app component
│   ├── package.json
│   └── tsconfig.json
├── docs/legacy-ui/        # Archived static HTML (not used by app)
└── README.md
```

## 🔌 API Endpoints

The backend provides the following endpoints:

- `GET /api/health` - Health check
- `GET /api/stats/overview` - Overview statistics
- `GET /api/stats/complexity-distribution` - Complexity distribution data
- `GET /api/stats/matching` - Matching statistics
- `GET /api/stats/field-reusability` - Field reusability analysis
- `GET /api/stats/complexity-trends` - Complexity trend analysis
- `GET /api/templates` - Paginated template list

## 📈 Database Statistics

Current database contains:
- 782 documents analyzed
- 11,653 fields tracked
- 1,094 Excel templates processed
- 1,082 successful matches (98.9% success rate)
- 858 precedents imported
- 858 manifest mappings created

## 🔧 Configuration

### Database Connection

Edit `server/.env` to configure database connection:

```env
PORT=3001
DB_HOST=localhost
DB_PORT=5432
DB_NAME=estimatedoc
DB_USER=estimatedoc_user
DB_PASSWORD=estimatedoc_user
```

### Frontend API URL

The frontend connects to `http://localhost:3001` by default. To change this, modify the `API_BASE` constant in:
- `dashboard.html` for standalone version
- `client/src/services/api.ts` for React version

## 📝 Development

### Running in Development Mode

```bash
# Terminal 1: Start backend
cd server
npm run dev

# Terminal 2: Start frontend (React)
cd client
npm start

# Legacy standalone HTML is archived under docs/legacy-ui and not part of the application.
```

### Building for Production

```bash
# Build backend
cd server
npm run build

# Build frontend
cd client
npm run build
```

## 🎨 Features Showcase

- **Real-time Updates**: Dashboard fetches live data from PostgreSQL
- **Responsive Charts**: All visualizations adapt to screen size
- **Color-coded Badges**: Visual indicators for complexity and confidence levels
- **Sortable Tables**: Template data with pagination support
- **Error Handling**: Graceful fallbacks for API failures

## 📊 Sample Data Insights

From the current dataset:
- **Simple** complexity: 974 templates (89%)
- **Moderate** complexity: 104 templates (9.5%)
- **Complex**: 4 templates (0.4%)
- **High Confidence Matches**: ~70%
- **Medium Confidence**: ~25%
- **Low Confidence**: ~5%

## 🚦 Status

✅ **Fully Functional** - The dashboard is 100% operational and ready for use.
