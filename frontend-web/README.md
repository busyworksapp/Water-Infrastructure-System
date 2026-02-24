# RandWater Web Control Room

Modern web-based SCADA control room for national water infrastructure monitoring.

## Features

- 🎯 Real-time sensor monitoring
- 🗺️ Interactive GIS mapping
- 🚨 Live alert notifications
- 📊 System statistics dashboard
- 🔐 Secure JWT authentication
- ⚡ WebSocket live updates
- 📱 Responsive design

## Quick Start

```bash
# Install dependencies
npm install

# Development
npm run dev

# Production build
npm run build

# Preview production build
npm run preview
```

## Environment Variables

Create `.env` file:
```
VITE_API_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000
```

## Tech Stack

- React 18
- Vite
- Leaflet (Maps)
- Axios
- React Router

## Deployment

See [WEB_DEPLOYMENT.md](../WEB_DEPLOYMENT.md) for deployment options.
