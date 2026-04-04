# Trishul Frontend Routes and Interactions

## Routes

- `/` — Landing
- `/operations` — Operations Dashboard
- `/reports` — Reports & Analytics

## Navigation behavior

- Desktop:
  - compact top header
  - left sidebar for `/operations` and `/reports`
  - sidebar starts expanded on each page load
- Mobile:
  - header menu button opens slide panel
  - panel closes by close button or overlay click

## Operations interactions

- Dynamic wizard step count follows selected attack template step count.
- Running state cards:
  - Attack Progress (progress + elapsed timer)
  - Attack Details (current step, target, module, status)
- Right column stack:
  - Live status stream
  - Findings list
  - Recent activity log

## Reports interactions

- KPI strip includes:
  - Pre-Attack Success Confidence
  - Live Attack Progress
  - Findings Velocity
  - Current Risk Index
- Filters:
  - target selector
  - attack type
  - severity
- Findings table actions:
  - View details (right-side drawer)
  - Mark reviewed
