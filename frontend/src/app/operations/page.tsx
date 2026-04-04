'use client';

import { AppScaffold } from '@/components/layout/app-scaffold';
import { OperationsPage } from '@/components/operations/operations-page';

export default function OperationsRoutePage() {
  return (
    <AppScaffold currentPage="operations" showSidebar>
      <OperationsPage />
    </AppScaffold>
  );
}
