# Trishul Frontend - Development Guide

## Quick Start

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Run setup script:**
   ```bash
   ./setup.sh
   ```
   
   Or manually:
   ```bash
   npm install
   npm run dev
   ```

3. **Open in browser:**
   ```
   http://localhost:3000
   ```

## Shell and page architecture

```
AppShell
├── AppHeader
├── MobileNavPanel (mobile)
├── SideNav (operations/reports)
├── LandingPage
├── OperationsPage
└── ReportsPage
```

## Design System

### Colors
- **Base**: #F5F5F7
- **Surface**: #E5E5EA
- **Strong/Text**: #1D1D1F

### Typography
- **Single family**: Inter

### Animations
- **Scroll reveal**: fade + 12px upward translate
- **Duration**: 220ms
- **Stagger**: 70ms
- **Trigger**: section in-view at 40%
- **Reduced motion**: no animation

## Integration Points

### Backend API (Planned wiring)

The UI is ready to connect to the Python backend via REST API:

```typescript
// Example API integration
const startScan = async (target: string) => {
  const response = await fetch('http://localhost:8000/api/v1/scans/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ target })
  });
  return response.json();
};
```

### Real-time updates

```typescript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  updateScanStatus(data);
};
```

## Next Steps for Development

1. **Backend integration contract**
   - Bind wizard steps and runtime status to real API payloads
   - Replace mock data contracts in `src/lib/mock-data.ts`

2. **Enhanced reporting**
   - Wire KPI and chart datasets to backend endpoints
   - Persist review state for findings

## File Structure Reference

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx          # Root layout with metadata
│   │   └── page.tsx            # Main page (renders AppShell)
│   ├── components/
│   │   ├── navigation/
│   │   ├── landing/
│   │   ├── operations/
│   │   ├── reports/
│   │   └── ui/
│   ├── lib/
│   │   ├── types.ts
│   │   ├── mock-data.ts
│   │   └── utils.ts
│   └── styles/
│       └── globals.css
├── package.json                # Dependencies
├── tailwind.config.ts          # Tailwind configuration
├── tsconfig.json              # TypeScript config
├── next.config.mjs            # Next.js config
├── postcss.config.mjs         # PostCSS config
├── setup.sh                   # Quick setup script
└── README.md                  # Documentation
```

## Troubleshooting

### Port Already in Use
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Or use different port
npm run dev -- -p 3001
```

### Module Not Found
```bash
# Clear cache and reinstall
rm -rf node_modules .next
npm install
```

### Build Errors
```bash
# Check TypeScript errors
npm run build

# Run type check
npx tsc --noEmit
```

## Performance Tips

- Use Next.js Image component for optimized images
- Lazy load heavy components
- Implement virtual scrolling for long lists
- Use React.memo for expensive renders

---

**Ready to build!** 🚀
