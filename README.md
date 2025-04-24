# LinkQ-Reimplementation

This project is a re-implementation of the research project presented in ["LinkQ: Answering Natural Language Questions over Knowledge Graphs with Query Templates"](https://ieeexplore.ieee.org/document/10771088). This project aims to provide an intuitive interface for querying knowledge graphs using natural language, with a focus on Wikidata as the primary knowledge source.

## Overview

LinkQ-Reimplementation is a web-based application that translates natural language questions into SPARQL queries for knowledge graph exploration. The project is built with React.js for the frontend and Python Flask for the backend. It features:

- Natural language to SPARQL query conversion
- Interactive query editor with syntax highlighting
- Real-time query execution against Wikidata
- Query history management
- Entity tooltips with detailed information
- Structured result display in table format

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Node.js 14.x or higher
- npm or yarn package manager

### Backend Setup

1. Navigate to the project root directory:
```bash
cd main_scripts
```

2. Create and activate a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend/linkq-frontend
```

2. Install Node.js dependencies:
```bash
npm install
```

### Running the Application

1. Start the backend server:
```bash
# From the main_scripts directory
python app.py
```

2. Start the frontend development server:
```bash
# From the frontend/linkq-frontend directory
npm start
```

The application will be available at `http://localhost:3000`

## Project Structure

```
linkq-reimplementation/
├── frontend/
│   └── linkq-frontend/
│       ├── src/
│       │   ├── components/      # React components
│       │   ├── hooks/          # Custom React hooks
│       │   ├── utils/          # Utility functions
│       │   └── App.js          # Main application component
│       ├── public/             # Static assets
│       └── package.json        # Frontend dependencies
│
└── main_scripts/
    ├── components/             # Backend components
    ├── utils/                  # Backend utilities
    ├── fuzzy_entity_search.py  # Entity search functionality
    └── extract_properties.py   # Property extraction logic

```

## Acknowledgments

- Original research paper: ["LinkQ: Answering Natural Language Questions over Knowledge Graphs with Query Templates"](https://ieeexplore.ieee.org/document/10771088)
- Wikidata for providing the knowledge graph infrastructure 