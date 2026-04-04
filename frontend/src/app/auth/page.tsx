'use client';

import { FormEvent, useState } from 'react';
import { useRouter } from 'next/navigation';
import { AppScaffold } from '@/components/layout/app-scaffold';
import { login, register } from '@/lib/api-client';
import { setToken } from '@/lib/auth';

export default function AuthPage() {
  const router = useRouter();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const payload = { email, password };
      const tokenResponse = mode === 'login' ? await login(payload) : await register(payload);
      setToken(tokenResponse.access_token);
      router.push('/operations');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppScaffold currentPage="auth" showSidebar={false}>
      <main className="mx-auto max-w-xl px-4 pb-16 pt-12 sm:px-6">
        <section className="surface-card p-6">
          <h2 className="text-2xl font-semibold text-[#1d1d1f]">{mode === 'login' ? 'Sign in' : 'Create account'}</h2>
          <p className="mt-1 text-sm text-[#6e6e73]">Connect UI to Trishul backend APIs with JWT authentication.</p>

          <div className="mt-4 inline-flex rounded-xl border border-[#d2d2d7] bg-[#f5f5f7] p-1">
            <button
              className={`rounded-lg px-3 py-1.5 text-sm ${mode === 'login' ? 'bg-white text-[#1d1d1f]' : 'text-[#6e6e73]'}`}
              onClick={() => setMode('login')}
              type="button"
            >
              Login
            </button>
            <button
              className={`rounded-lg px-3 py-1.5 text-sm ${mode === 'register' ? 'bg-white text-[#1d1d1f]' : 'text-[#6e6e73]'}`}
              onClick={() => setMode('register')}
              type="button"
            >
              Register
            </button>
          </div>

          <form className="mt-5 space-y-3" onSubmit={onSubmit}>
            <label className="block text-sm">
              <span className="mb-1 block text-[#6e6e73]">Email</span>
              <input
                className="h-10 w-full rounded-xl border border-[#d2d2d7] bg-white px-3 text-sm text-[#1d1d1f] outline-none"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </label>
            <label className="block text-sm">
              <span className="mb-1 block text-[#6e6e73]">Password</span>
              <input
                className="h-10 w-full rounded-xl border border-[#d2d2d7] bg-white px-3 text-sm text-[#1d1d1f] outline-none"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </label>
            {error ? <p className="text-sm text-red-600">{error}</p> : null}
            <button
              className="h-10 rounded-xl bg-[#1d1d1f] px-4 text-sm font-medium text-white disabled:opacity-60"
              type="submit"
              disabled={loading}
            >
              {loading ? 'Please wait...' : mode === 'login' ? 'Sign in' : 'Create account'}
            </button>
          </form>
        </section>
      </main>
    </AppScaffold>
  );
}
