# 🔱 Trishul Frontend - Quick Start Guide

## Instant Setup (3 Steps)

```bash
# 1. Go to frontend folder
cd frontend

# 2. Install & Run
./setup.sh

# 3. Done! Open browser
# http://localhost:3000
```

## What You Get

### Visual Design
- **Monochrome Theme**: White, black, and space gray
- **Clean Layout**: Minimal enterprise interface
- **Subtle Motion**: Scroll-reveal cards with reduced-motion support

### Page Structure
```
Landing
Operations Dashboard
Reports / Analytics
```

### Features
- ✅ Unified frontend shell
- ✅ Dynamic attack-step wizard
- ✅ Real-time operation and KPI panels
- ✅ Fully responsive
- ✅ TypeScript typed
- ✅ Production ready

## File Locations

```
frontend/
├── src/components/app-shell.tsx          ← Main shell (edit here)
├── src/components/landing/               ← Landing page components
├── src/components/operations/            ← Operations page components
├── src/components/reports/               ← Reports page components
├── src/styles/globals.css                ← Global styles
└── package.json                          ← Dependencies

Documentation:
├── README.md          ← User guide
├── DEVELOPMENT.md     ← Developer guide  
├── BUILD_SUMMARY.md   ← Build overview
└── COMMANDS.md        ← Command reference
```

## Customize

### Add New Command
Edit `src/lib/mock-data.ts` to add or update workflow data and findings.

### Change Colors
Edit `tailwind.config.ts`:
```typescript
theme: {
  extend: {
    colors: {
      primary: '#YOUR_COLOR',
    }
  }
}
```

### Modify Layout
Edit `src/components/app-shell.tsx`

## Connect to Backend

### Option 1: Next.js API Routes
Create `src/app/api/scans/route.ts`:
```typescript
export async function POST(request: Request) {
  const payload = await request.json();
  // Call Python backend
  const response = await fetch('http://localhost:8000/api/v1/scans/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  return Response.json(await response.json());
}
```

### Option 2: Direct Fetch
In page components:
```typescript
const handleScan = async () => {
  const res = await fetch('http://localhost:8000/api/v1/scans/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ target: 'example.com' })
  });
  const data = await res.json();
  // Update UI
};
```

## Troubleshooting

### Port in use?
```bash
# Use different port
npm run dev -- -p 3001
```

### Dependencies issue?
```bash
rm -rf node_modules .next
npm install
```

### TypeScript errors?
```bash
npm run build
```

## Pro Tips

1. **Type `//`** to see all commands instantly
2. **Press Enter** to send, **Shift+Enter** for new line
3. **Edit app-shell and page components** for most customizations
4. **Check COMMANDS.md** for future command ideas
5. **Read DEVELOPMENT.md** for detailed integration guide

## Next Steps

1. ✅ UI is ready
2. ⏳ Connect to Python backend
3. ⏳ Add real-time scan updates
4. ⏳ Implement vulnerability cards
5. ⏳ Add report generation

---

**Ready to hack!** 🚀 The frontend is in `/frontend/` folder.

For detailed info: Check `/frontend/DEVELOPMENT.md`
