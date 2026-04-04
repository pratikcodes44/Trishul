'use client';

import { AppScaffold } from '@/components/layout/app-scaffold';
import { LandingPage } from '@/components/landing/landing-page';

export default function Home() {
  return (
    <AppScaffold currentPage="landing" showSidebar={false}>
      <LandingPage />
    </AppScaffold>
  );
}
