# AMRS Maintenance Tracker - React Frontend

This is the React-based frontend for the AMRS Maintenance Tracker desktop application.

## Tech Stack

- **React 18** with TypeScript
- **Ant Design** for UI components
- **React Router** for navigation
- **React Query** for API state management
- **Vite** for fast development and optimized builds

## Development

### Prerequisites

- Node.js 18+ and npm

### Install Dependencies

```bash
npm install
```

### Development Server

```bash
npm run dev
```

The dev server will start on `http://localhost:3000` and proxy API requests to Flask on `http://localhost:5000`.

### Build for Production

```bash
npm run build
```

Builds the app for production to the `dist` folder.

### Lint

```bash
npm run lint
```

### Test

```bash
npm test
```

## Project Structure

```
frontend/
├── src/
│   ├── components/      # Reusable components
│   │   ├── auth/       # Authentication components
│   │   ├── common/     # Common/shared components
│   │   ├── dashboard/  # Dashboard components
│   │   └── ...
│   ├── contexts/       # React contexts
│   ├── pages/          # Page components
│   ├── hooks/          # Custom React hooks
│   ├── api/            # API client functions
│   ├── utils/          # Utility functions
│   ├── styles/         # CSS files
│   ├── types/          # TypeScript type definitions
│   ├── App.tsx         # Main App component
│   └── main.tsx        # Application entry point
├── public/             # Static assets
├── index.html          # HTML template
├── vite.config.ts      # Vite configuration
├── tsconfig.json       # TypeScript configuration
└── package.json        # Dependencies and scripts
```

## Integration with Electron

The frontend is designed to work both:
- As a standalone web application
- Embedded in the Electron desktop wrapper

Electron-specific features (like window controls) are conditionally enabled when `window.electronAPI` is available.

## API Integration

The frontend communicates with the Flask backend via REST API endpoints at `/api/v1/`.

Key endpoints:
- `/api/v1/auth/login` - User authentication
- `/api/v1/auth/logout` - User logout
- `/api/v1/auth/me` - Get current user
- `/api/v1/dashboard` - Dashboard statistics
- And more...

## Development Notes

### Phase 1 Status (Current)

- ✅ Project setup with TypeScript and Ant Design
- ✅ React Router configuration
- ✅ Auth Context implementation
- ✅ Login page with error handling
- ✅ Custom title bar component
- ✅ Desktop menu bar
- ✅ Sidebar navigation
- ✅ Basic Dashboard page
- ✅ Splash screen component
- ⏸️ Electron integration (pending)
- ⏸️ Additional pages (Phase 2)

### Next Steps

1. Complete Electron main.js integration for frameless window
2. Implement keyboard shortcuts
3. Build out remaining pages (Machines, Maintenance, Audits, etc.)
4. Implement virtual scrolling for large datasets
5. Add accessibility features

## Contributing

When adding new components or features:
1. Follow the existing code structure
2. Use TypeScript for type safety
3. Write tests for new functionality
4. Update this README if adding new major features
