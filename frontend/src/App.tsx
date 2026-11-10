import { Fragment, useCallback, useEffect, useMemo, useRef, useState, type FormEvent, type CSSProperties, type ReactNode, type MouseEvent as ReactMouseEvent } from 'react';
import { createPortal } from 'react-dom';
import { api } from './api';
import { cloudAuthEnabled, confirmSignUp, confirmPasswordReset, requestPasswordReset, restoreSession, sessionToken, SessionUser, signIn, signOut, signUp } from './auth';
import type { Analysis, AnalysisJob, Finding, Severity } from './types';

type Page = 'Home' | 'New analysis' | 'Findings' | 'Architecture' | 'Ask Sentinal' | 'History' | 'Settings' | 'Profile';
type ThemePreference = 'light';
type ProfileData = { full_name: string; username: string; headline: string; bio: string; location: string; website: string; email: string; email_public: boolean; github_username: string; github_url: string; preferred_languages: string[]; technical_skills: string[]; interests: string[]; role: string; avatar_data_url: string; default_dashboard: string; notifications_enabled: boolean; privacy_profile_public: boolean; created_at: string; updated_at: string };
type GitHubOverview = { login: string; name: string | null; avatar_url: string; html_url: string; public_repos: number; followers: number; following: number; bio: string | null; repositories: { name: string; html_url: string; description: string | null; language: string | null; stargazers_count: number; updated_at: string }[] };
const emptyProfile = (username = ''): ProfileData => ({ full_name: '', username: username.includes('@') ? username.split('@')[0] : username, headline: '', bio: '', location: '', website: '', email: username.includes('@') ? username : '', email_public: false, github_username: '', github_url: '', preferred_languages: [], technical_skills: [], interests: [], role: '', avatar_data_url: '', default_dashboard: 'Home', notifications_enabled: true, privacy_profile_public: false, created_at: '', updated_at: '' });
function formatTimestamp(value: unknown): string {
  if (typeof value !== 'string' || !value.trim()) return 'Time not recorded';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Time unavailable' : date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
}
type Props = { label: string; value: string; caption: string; icon: string; tone?: 'teal' | 'orange' | 'navy' | 'violet' };
type ChatMessage = { role: 'user' | 'assistant'; content: string };

const NAV_ITEMS: { label: Page; icon: string; note: string }[] = [
  { label: 'Home', icon: 'home', note: 'Workspace home' },
  { label: 'New analysis', icon: 'scan', note: 'Analyze a repository' },
  { label: 'Findings', icon: 'shield', note: 'Evidence and remediation' },
  { label: 'Architecture', icon: 'network', note: 'Repository relationships' },
  { label: 'Ask Sentinal', icon: 'sparkles', note: 'Ask about your snapshot' },
  { label: 'History', icon: 'history', note: 'Previous snapshots' },
  { label: 'Settings', icon: 'settings', note: 'Preferences and access' },
  { label: 'Profile', icon: 'user-round', note: 'Developer profile' },
];
const MOBILE_PRIMARY_NAV = new Set<Page>(['Home', 'New analysis', 'Findings', 'History']);
type AppIconName = string;

function AppIcon({ name, size = 18 }: { name: string; size?: number }) {
  const common = { fill: 'none', stroke: 'currentColor', strokeWidth: 2.15, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const };
  let glyph;
  switch (name as AppIconName) {
    case 'home': glyph = <><path d="m3.5 10.5 8.5-7 8.5 7"/><path d="M5.5 9.5v10h13v-10"/><path d="M9.5 19.5v-6h5v6"/></>; break;
    case 'scan': glyph = <><path d="M8 4H5a2 2 0 0 0-2 2v3"/><path d="M16 4h3a2 2 0 0 1 2 2v3"/><path d="M21 15v3a2 2 0 0 1-2 2h-3"/><path d="M3 15v3a2 2 0 0 0 2 2h3"/><circle cx="11" cy="11" r="4.5"/><path d="m14.5 14.5 4 4"/></>; break;
    case 'shield': glyph = <><path d="M12 3 20 6v5.2c0 4.6-3.1 7.9-8 9.8-4.9-1.9-8-5.2-8-9.8V6z"/><path d="m8.5 12 2.3 2.3 4.8-5"/></>; break;
    case 'network': glyph = <><rect x="9" y="3" width="6" height="5" rx="1.3"/><rect x="2.5" y="16" width="6" height="5" rx="1.3"/><rect x="15.5" y="16" width="6" height="5" rx="1.3"/><path d="M12 8v4M5.5 16v-4h13v4"/></>; break;
    case 'sparkles': glyph = <><path d="m12 3 1.5 5.5L19 10l-5.5 1.5L12 17l-1.5-5.5L5 10l5.5-1.5z"/><path d="m19 15 .8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/><path d="m5 3 .6 1.8L7.5 5.5l-1.9.7L5 8l-.6-1.8-1.9-.7 1.9-.7z"/></>; break;
    case 'history': glyph = <><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2"/><path d="M4.2 5.5 2.8 8.2"/></>; break;
    case 'settings': glyph = <><circle cx="12" cy="12" r="3.1"/><path d="m19.4 15 .1.1 1.1 1.1-1.8 3.1-1.6-.5a7.9 7.9 0 0 1-1.9 1.1l-.3 1.7h-3.6l-.3-1.7a7.9 7.9 0 0 1-1.9-1.1l-1.6.5-1.8-3.1L7 15a7.7 7.7 0 0 1 0-2l-1.1-1.2 1.8-3.1 1.6.5a7.9 7.9 0 0 1 1.9-1.1l.3-1.7h3.6l.3 1.7a7.9 7.9 0 0 1 1.9 1.1l1.6-.5 1.8 3.1-1.1 1.2a7.7 7.7 0 0 1-.1 2Z" transform="translate(-1.4 -1.4) scale(.98)"/></>; break;
    case 'sun': glyph = <><circle cx="12" cy="12" r="4"/><path d="M12 2v2.2M12 19.8V22M4.9 4.9l1.6 1.6m11 11 1.6 1.6M2 12h2.2m15.6 0H22M4.9 19.1l1.6-1.6m11-11 1.6-1.6"/></>; break;
    case 'moon': glyph = <path d="M20.5 14A8.5 8.5 0 0 1 10 3.5 8.6 8.6 0 1 0 20.5 14Z"/>; break;
    case 'download': glyph = <><path d="M12 3v12"/><path d="m7 10 5 5 5-5"/><path d="M4 19v2h16v-2"/></>; break;
    case 'play': glyph = <path d="m8 5 11 7-11 7z"/>; break;
    case 'more-horizontal': glyph = <><circle cx="5" cy="12" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="19" cy="12" r="1.6"/></>; break;
    case 'arrow-up-right': glyph = <><path d="M7 17 17 7"/><path d="M8 7h9v9"/></>; break;
    case 'log-out': glyph = <><path d="M10 17l5-5-5-5"/><path d="M15 12H3"/><path d="M12 3h6a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-6"/></>; break;
    case 'check': glyph = <path d="m5 12 4.5 4.5L19 7"/>; break;
    case 'lock': glyph = <><rect x="4" y="10" width="16" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/></>; break;
    case 'mail': glyph = <><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m4 7 8 6 8-6"/></>; break;
    case 'file': glyph = <><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 13h8M8 17h8"/></>; break;
    case 'calendar': glyph = <><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18"/></>; break;
    case 'plus': glyph = <><path d="M12 5v14M5 12h14"/></>; break;
    case 'chevron-down': glyph = <path d="m6 9 6 6 6-6"/>; break;
    case 'user-round': glyph = <><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></>; break;
    case 'user': glyph = <><circle cx="12" cy="8" r="3.5"/><path d="M5 20a7 7 0 0 1 14 0"/></>; break;
    case 'code': glyph = <><path d="m8 8-4 4 4 4M16 8l4 4-4 4M14 4l-4 16"/></>; break;
    case 'git-branch': glyph = <><circle cx="6" cy="4" r="2"/><circle cx="6" cy="20" r="2"/><circle cx="18" cy="6" r="2"/><path d="M6 6v12M18 8a6 6 0 0 1-6 6H6"/></>; break;
    case 'briefcase': glyph = <><rect x="3" y="7" width="18" height="14" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M3 12h18M10 12v2h4v-2"/></>; break;
    case 'map-pin': glyph = <><path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="2.5"/></>; break;
    case 'globe': glyph = <><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a15 15 0 0 1 0 18M12 3a15 15 0 0 0 0 18"/></>; break;
    case 'image': glyph = <><rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="8.5" cy="9" r="1.5"/><path d="m21 15-5-5L5 20"/></>; break;
    case 'save': glyph = <><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2Z"/><path d="M17 21v-8H7v8M7 3v5h8"/></>; break;
    case 'external-link': glyph = <><path d="M13 5h6v6M19 5l-9 9"/><path d="M19 13v5a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h5"/></>; break;
    case 'monitor': glyph = <><rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 21h8M12 17v4"/></>; break;
    case 'laptop': glyph = <><rect x="5" y="4" width="14" height="11" rx="1.5"/><path d="M2 19h20l-2-4H4l-2 4Z"/></>; break;
    case 'palette': glyph = <><path d="M12 3a9 9 0 1 0 0 18h1.5a2.5 2.5 0 0 0 1.7-4.3 1.8 1.8 0 0 1 1.3-3.1h1a2.5 2.5 0 0 0 2.5-2.5A8.1 8.1 0 0 0 12 3Z"/><circle cx="7.5" cy="11" r="1"/><circle cx="10" cy="7.5" r="1"/><circle cx="15" cy="8" r="1"/></>; break;
    case 'bell': glyph = <><path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/></>; break;
    case 'x': glyph = <><path d="m6 6 12 12M18 6 6 18"/></>; break;
    case 'arrow-left': glyph = <><path d="M19 12H5M12 19l-7-7 7-7"/></>; break;
    default: glyph = <><circle cx="12" cy="12" r="8"/><path d="M8 12h8"/></>;
  }
  return <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" focusable="false" {...common}>{glyph}</svg>;
}

function ThemePreferenceControl() { return <span className="light-mode-indicator"><AppIcon name="sun" size={15}/> Light interface</span>; }

function TiltSurface({ children, className = '' }: { children: ReactNode; className?: string }) {
  const [tilt, setTilt] = useState({ x: 0, y: 0 });
  const handleMove = (event: ReactMouseEvent<HTMLElement>) => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches || !window.matchMedia('(pointer: fine)').matches) return;
    const bounds = event.currentTarget.getBoundingClientRect();
    setTilt({ x: -((event.clientY - bounds.top) / bounds.height - .5) * 3.2, y: ((event.clientX - bounds.left) / bounds.width - .5) * 3.2 });
  };
  return <article className={`tilt-surface ${className}`} onMouseMove={handleMove} onMouseLeave={() => setTilt({ x: 0, y: 0 })} style={{ '--tilt-x': `${tilt.x}deg`, '--tilt-y': `${tilt.y}deg` } as CSSProperties}>{children}</article>;
}

const SEVERITIES: Severity[] = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'];
const SEVERITY_COLOURS: Record<Severity, string> = { CRITICAL: '#800020', HIGH: '#FF6B6B', MEDIUM: '#FF8C00', LOW: '#006D77', INFO: '#1E3A8A' };

function MetricCard({ label, value, caption, icon, tone = 'teal' }: Props) {
  return <TiltSurface className={`metric-card tone-${tone}`}><div className="metric-top"><span className="metric-icon"><AppIcon name={icon} size={19}/></span><span className="metric-label">{label}</span></div><div className="metric-value">{value}</div><div className="metric-caption">{caption}</div></TiltSurface>;
}

function Brand({ inverse = false }: { inverse?: boolean }) {
  return <div className={`brand ${inverse ? 'brand-inverse' : ''}`}><span className="brand-mark"><span></span><span></span><span></span><span></span></span><span className="brand-word">sentinal<span className="brand-period">.</span></span></div>;
}

function CubeIllustration() {
  const cubes = [{x:192,y:66,c:'#FF8C00'},{x:242,y:91,c:'#F5E6CA'},{x:292,y:66,c:'#FF8C00'},{x:142,y:91,c:'#F5E6CA'},
    {x:192,y:116,c:'#006D77'},{x:242,y:141,c:'#F5E6CA'},{x:292,y:116,c:'#006D77'},{x:242,y:41,c:'#F5E6CA'},
    {x:75,y:205,c:'#006D77'},{x:125,y:230,c:'#F5E6CA'},{x:175,y:205,c:'#F5E6CA'},{x:365,y:205,c:'#0B3155'}];
  return <svg className="cube-illustration" viewBox="0 0 480 300" role="img" aria-label="Isometric geometric code blocks illustration">
    <g stroke="#0D1B2A" strokeWidth="1.5" strokeLinejoin="round">
      <path d="M160 120 L245 77 L330 120 L245 166 Z" fill="#e3dfd4"/><path d="M160 120 L160 142 L245 188 L245 166 Z" fill="#c4c2bb"/><path d="M245 166 L330 120 L330 142 L245 188 Z" fill="#ddd9cf"/>
      <path d="M145 140 L245 190 L345 140 L245 91 Z" fill="#f4f1e6"/><path d="M145 140 L145 154 L245 205 L245 190 Z" fill="#c8c7c1"/><path d="M245 190 L345 140 L345 154 L245 205 Z" fill="#dedbd1"/>
      {cubes.slice(0,8).map((cube,i)=><g key={i} transform={`translate(${cube.x} ${cube.y})`}><path d="M0 -24 L24 -11 L0 2 L-24 -11 Z" fill={cube.c}/><path d="M-24 -11 L0 2 L0 28 L-24 15 Z" fill={cube.c==='#F5E6CA'?'#fffdf5':cube.c}/><path d="M0 2 L24 -11 L24 15 L0 28 Z" fill={cube.c==='#FF8C00'?'#e57700':cube.c==='#006D77'?'#00545c':cube.c}/></g>)}
      {cubes.slice(8).map((cube,i)=><g key={i} transform={`translate(${cube.x} ${cube.y})`}><path d="M0 -24 L24 -11 L0 2 L-24 -11 Z" fill={cube.c}/><path d="M-24 -11 L0 2 L0 28 L-24 15 Z" fill="#e4e1d7"/><path d="M0 2 L24 -11 L24 15 L0 28 Z" fill={cube.c}/></g>)}
    </g>
    <circle cx="390" cy="75" r="4" fill="#006D77"/><circle cx="409" cy="59" r="2.5" fill="#FF8C00"/><path d="M387 92 L410 92" stroke="#006D77" strokeWidth="2" strokeLinecap="round"/>
  </svg>;
}

function LoginScreen({ onLogin, themePreference, onThemeChange }: { onLogin: (user: SessionUser) => void; themePreference: ThemePreference; onThemeChange: (value: ThemePreference) => void }) {
  const [mode, setMode] = useState<'signin' | 'signup' | 'confirm' | 'reset' | 'reset-confirm'>('signin');
  const [email, setEmail] = useState(() => localStorage.getItem('sentinal-remembered-email') || ''); const [password, setPassword] = useState(''); const [code, setCode] = useState(''); const [rememberEmail, setRememberEmail] = useState(() => localStorage.getItem('sentinal-remember-email-enabled') === '1');
  const [busy, setBusy] = useState(false); const [error, setError] = useState(''); const [message, setMessage] = useState('');
  const submit = async (e: FormEvent) => {
    e.preventDefault(); setBusy(true); setError(''); setMessage('');
    if (mode === 'signin') { if (rememberEmail) { localStorage.setItem('sentinal-remembered-email', email.trim()); localStorage.setItem('sentinal-remember-email-enabled', '1'); } else { localStorage.removeItem('sentinal-remembered-email'); localStorage.removeItem('sentinal-remember-email-enabled'); } }
    try {
      if (mode === 'signin') { const user = await signIn(email.trim(), password); onLogin(user); }
      else if (mode === 'signup') { await signUp(email.trim(), password); setMode('confirm'); setMessage('A verification code has been sent to your email address.'); }
      else if (mode === 'confirm') { await confirmSignUp(email.trim(), code.trim()); setMode('signin'); setCode(''); setPassword(''); setMessage('Email verified. Sign in to continue.'); }
      else if (mode === 'reset') { await requestPasswordReset(email.trim()); setMode('reset-confirm'); setMessage('A password reset code has been sent to your email address.'); }
      else { await confirmPasswordReset(email.trim(), code.trim(), password); setMode('signin'); setCode(''); setPassword(''); setMessage('Password updated. Sign in with your new password.'); }
    } catch (err) { setError(err instanceof Error ? err.message : 'Authentication failed.'); }
    finally { setBusy(false); }
  };
  const localLogin = () => onLogin({ username: 'Local workspace', localMode: true });
  return <div className="login-shell">
    <header className="login-top"><Brand/><div className="login-top-actions"><span className="micro-label">CODEBASE INTELLIGENCE</span><ThemePreferenceControl/></div></header>
    <main className="login-main">
      <section className="login-copy"><span className="eyebrow"><span className="eyebrow-dot"></span> YOUR CODEBASE WORKSPACE</span>
        <h1>Understand Your Code.<br/><em>Prove Every Decision.</em></h1>
        <p className="login-lede">An AI-powered code intelligence platform that analyzes repositories, traces code flows, uncovers security risks, and turns complex codebases into actionable engineering insights.</p>
        <div className="login-rule"></div>
        <form className="login-form" onSubmit={submit}>
          <div className="login-form-heading"><h2>{mode === 'signin' ? 'Welcome back' : mode === 'signup' ? 'Create your account' : mode === 'reset' || mode === 'reset-confirm' ? 'Reset your password' : 'Verify your email'}</h2><span>{cloudAuthEnabled ? 'SECURE ACCESS' : 'SETUP REQUIRED'}</span></div>
          {mode === 'confirm' || mode === 'reset-confirm' ? <>
            <p className="auth-context">Enter the verification code sent to <strong>{email}</strong>.</p>
            <label className="field-label" htmlFor="login-code">Verification code</label><input id="login-code" className="text-input login-input" inputMode="numeric" autoComplete="one-time-code" value={code} onChange={e=>setCode(e.target.value)} placeholder="Enter your email code" required />
            {mode === 'reset-confirm' && <><label className="field-label" htmlFor="login-password">New password</label><input id="login-password" className="text-input login-input" type="password" autoComplete="new-password" minLength={8} value={password} onChange={e=>setPassword(e.target.value)} placeholder="At least 8 characters" required /></>}
          </> : <>
            <label className="field-label" htmlFor="login-email">Email address</label><input id="login-email" className="text-input login-input" type="email" autoComplete="email" value={email} onChange={e=>setEmail(e.target.value)} placeholder="you@company.com" required />
            {mode !== 'reset' && <><label className="field-label" htmlFor="login-password">Password</label><input id="login-password" className="text-input login-input" type="password" autoComplete={mode === 'signin' ? 'current-password' : 'new-password'} minLength={8} value={password} onChange={e=>setPassword(e.target.value)} placeholder="At least 8 characters" required /></>}
            {mode === 'signin' && <label className="remember-email-row"><input type="checkbox" checked={rememberEmail} onChange={event => setRememberEmail(event.target.checked)}/><span>Remember my email on this device</span></label>}
          </>}
          {error && <div className="notice notice-error" role="alert">{error}</div>}{message && <div className="notice notice-success" role="status">{message}</div>}
          <button className="btn btn-primary login-submit" disabled={busy || !cloudAuthEnabled}>{busy ? 'Please wait…' : mode === 'signin' ? 'Sign in securely' : mode === 'signup' ? 'Create account' : mode === 'reset' ? 'Send reset code' : mode === 'reset-confirm' ? 'Update password' : 'Confirm email'}<AppIcon name="arrow-up-right" size={17}/></button>
          {cloudAuthEnabled && <div className="auth-switch">{mode === 'signin' ? <><button type="button" onClick={()=>{setMode('reset');setError('');setMessage('')}}>Forgot password?</button><span>New to Sentinal? <button type="button" onClick={()=>{setMode('signup');setError('');setMessage('')}}>Create an account</button></span></> : <button type="button" onClick={()=>{setMode('signin');setError('');setMessage('');setCode('');setPassword('')}}>Back to sign in</button>}</div>}
        </form>
        {!cloudAuthEnabled && <div className="dev-access-panel"><span className="dev-access-icon"><AppIcon name="lock" size={18}/></span><div><strong>{import.meta.env.DEV ? 'Authentication is not configured here' : 'Sign-in is not enabled for this deployment'}</strong><p>{import.meta.env.DEV ? 'This local setup has no Cognito User Pool configured. You can continue into the local workspace while developing; no account is created.' : 'Configure an Amazon Cognito User Pool and client ID to enable secure sign-in for this deployment.'}</p></div>{import.meta.env.DEV && <button className="btn btn-outline dev-access-button" type="button" onClick={localLogin}>Continue to local workspace <AppIcon name="arrow-up-right" size={16}/></button>}</div>}
        <div className="login-footnote"><span>●</span> No code is executed during default analysis. Reports keep evidence and uncertainty visible.</div>
      </section>
      <section className="login-art-panel"><div className="art-stamp">S / 01<br/><span>ANALYZE</span></div><CubeIllustration/><div className="art-caption"><span>01 — READ</span><span>02 — CORRELATE</span><span>03 — EXPLAIN</span></div><div className="art-baseline"></div><p>Clarity for every codebase.</p></section>
    </main>
    <footer className="login-footer"><span>© SENTINAL / CODEBASE INTELLIGENCE</span><span>BUILT FOR DEVELOPERS & MENTORS</span><span>LOCAL-FIRST · COST-CONSCIOUS</span></footer>
  </div>;
}

function SeverityPill({ severity }: { severity: string }) { return <span className={`severity-pill sev-${severity.toLowerCase()}`}><span></span>{severity}</span>; }

function LanguageChart({ analysis }: { analysis?: Analysis | null }) {
  const languages = analysis?.languages || [];
  const total = languages.reduce((a, l) => a + l.loc, 0);
  return <div className="language-chart">
    {!analysis || languages.length === 0 ? <div className="chart-empty"><span className="empty-mark">∅</span><strong>No language data yet</strong><small>Analyze a project to populate this chart.</small></div> : <>
      <div className="lang-stacked">{languages.map((l,i)=><span key={l.name} title={`${l.name}: ${l.loc} lines`} style={{ width: `${total ? l.loc / total * 100 : 0}%`, background: ['#006D77','#FF8C00','#1E3A8A','#4B0082','#A7C957','#FF6B6B','#00C2CB'][i%7] }} />)}</div>
      <div className="lang-legend">{languages.slice(0,7).map((l,i)=><div key={l.name} className="lang-row"><span className="legend-swatch" style={{background:['#006D77','#FF8C00','#1E3A8A','#4B0082','#A7C957','#FF6B6B','#00C2CB'][i%7]}}></span><span className="lang-name">{l.name}</span><span className="lang-files">{l.files} files</span><strong>{l.loc.toLocaleString()}</strong></div>)}</div>
    </>}
  </div>;
}

function SeverityDonut({ analysis }: { analysis?: Analysis | null }) {
  const counts = analysis?.severity_counts; const total = counts ? SEVERITIES.reduce((sum,s)=>sum+(counts[s]||0),0) : 0;
  const segments = total ? SEVERITIES.filter(s=>(counts?.[s]||0)>0).map(s=>({severity:s,count:counts![s]})) : [];
  let accumulated = 0;
  const gradient = segments.map(s=>{const start=accumulated;accumulated+=s.count/total*100;return `${SEVERITY_COLOURS[s.severity]} ${start}% ${accumulated}%`;}).join(', ');
  return <div className="severity-visual"><div className={`donut ${total ? '' : 'donut-empty'}`} style={total ? {background:`conic-gradient(${gradient})`} : undefined}><div className="donut-center"><strong>{total || '—'}</strong><span>findings</span></div></div><div className="severity-legend">{SEVERITIES.map(s=><div className="severity-legend-row" key={s}><span className="legend-swatch" style={{background:SEVERITY_COLOURS[s]}}></span><span>{s}</span><strong>{counts?.[s] ?? '—'}</strong></div>)}</div></div>;
}

function FileBarChart({ analysis }: { analysis?: Analysis | null }) {
  const files = analysis?.files.slice(0,7) || []; const max = Math.max(1,...files.map(f=>f.loc));
  if (!analysis) return <div className="chart-empty"><span className="empty-mark">⌁</span><strong>Awaiting a source snapshot</strong><small>Largest files will appear after analysis.</small></div>;
  return <div className="file-bars">{files.map((file,i)=><div className="file-bar-row" key={file.path}><div className="file-bar-label" title={file.path}>{file.path.split('/').pop()}</div><div className="file-bar-track"><span style={{width:`${file.loc/max*100}%`,background:i%2===0?'#006D77':'#FF8C00'}}></span></div><strong>{file.loc}</strong></div>)}</div>;
}

function ArchitectureMap({ analysis }: { analysis?: Analysis | null }) {
  const [selectedPath, setSelectedPath] = useState('');
  const [search, setSearch] = useState('');
  const nodes = useMemo(() => {
    const sourceNodes = analysis?.architecture.nodes?.length
      ? analysis.architecture.nodes
      : (analysis?.files || []).map(file => ({ id: file.path, language: file.language }));
    return sourceNodes.filter(node => node.id.toLowerCase().includes(search.toLowerCase())).slice(0, 20);
  }, [analysis, search]);
  const edges = analysis?.architecture.edges || [];
  const width = 960;
  const columns = 4;
  const rowCount = Math.max(1, Math.ceil(nodes.length / columns));
  const height = Math.max(190, 86 + rowCount * 98);
  const positions = new Map(nodes.map((node, i) => [node.id, { x: 112 + (i % columns) * 240, y: 53 + Math.floor(i / columns) * 98 }]));
  const visibleEdges = edges.filter(edge => positions.has(edge.source) && positions.has(edge.target)).slice(0, 70);
  const activePath = selectedPath && nodes.some(node => node.id === selectedPath)
    ? selectedPath : nodes[0]?.id || '';
  const activeFile = analysis?.files.find(file => file.path === activePath);
  const activeFindings = (analysis?.findings || []).filter(finding => finding.path === activePath);
  const activeHigh = activeFindings.filter(finding => finding.severity === 'CRITICAL' || finding.severity === 'HIGH').length;
  const getFindings = (path: string) => (analysis?.findings || []).filter(finding => finding.path === path);

  if (!analysis) return <div className="empty-panel"><span className="empty-mark">⌘</span><h3>Your repository map is waiting</h3><p>Run an analysis to explore inferred file-to-file imports and inspect evidence attached to each file.</p></div>;

  return <div className="atlas-workspace">
    <div className="atlas-toolbar">
      <div><span className="section-index">INTERACTIVE DEPENDENCY MAP</span><p>Choose a node to inspect its measured size and linked findings.</p></div>
      <label className="atlas-search"><span>⌕</span><input type="search" value={search} onChange={event => setSearch(event.target.value)} placeholder="Find a file…" aria-label="Search architecture files" /></label>
    </div>
    <div className="atlas-canvas-shell">
      <div className="atlas-canvas-scroll"><div className="architecture-canvas">
        {nodes.length ? <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Interactive static dependency graph">
          <defs><marker id="atlas-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#b7aabb" /></marker></defs>
          {visibleEdges.map((edge, index) => {
            const from = positions.get(edge.source)!; const to = positions.get(edge.target)!;
            const highlighted = edge.source === activePath || edge.target === activePath;
            const startY = from.y + 27; const endY = to.y - 27;
            const mid = (startY + endY) / 2;
            return <path key={`${edge.source}-${edge.target}-${index}`} d={`M ${from.x} ${startY} C ${from.x} ${mid}, ${to.x} ${mid}, ${to.x} ${endY}`} fill="none" stroke={highlighted ? '#EE7657' : '#CFC6D6'} strokeWidth={highlighted ? 2.2 : 1.2} opacity={highlighted ? 1 : .72} markerEnd="url(#atlas-arrow)" />;
          })}
          {nodes.map(node => {
            const pos = positions.get(node.id)!; const count = getFindings(node.id).length;
            const selected = node.id === activePath;
            const fill = selected ? '#FFF0E9' : count ? '#FFF7F3' : '#FFFFFF';
            const displayName = node.id.split('/').pop() || node.id;
            return <g key={node.id} className="atlas-node" role="button" tabIndex={0} aria-label={`Inspect ${node.id}, ${count} findings`} aria-pressed={selected}
              onClick={() => setSelectedPath(node.id)} onKeyDown={event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); setSelectedPath(node.id); } }}>
              <rect x={pos.x - 101} y={pos.y - 27} width="202" height="54" rx="13" fill={fill} stroke={selected ? '#EE7657' : count ? '#E7A38E' : '#E6E0E9'} strokeWidth={selected ? 2.2 : 1.1}/>
              <circle cx={pos.x - 84} cy={pos.y - 8} r="4.5" fill={count ? '#E56F5B' : '#51A68B'} />
              <text x={pos.x - 72} y={pos.y - 5} fill="#302B35" fontSize="11" fontWeight="600">{displayName.slice(0, 22)}{displayName.length > 22 ? '…' : ''}</text>
              <text x={pos.x - 84} y={pos.y + 13} fill="#817987" fontSize="8.8">{node.language} · {count ? `${count} finding${count === 1 ? '' : 's'}` : 'no current finding'}</text>
            </g>;
          })}
        </svg> : <div className="atlas-empty"><strong>No mappable source modules were detected.</strong><span>Files are still available in the analysis inventory below.</span></div>}
      </div></div>
      <div className="atlas-map-footer"><span><i className="atlas-dot atlas-dot-risk"/> File has one or more findings</span><span><i className="atlas-dot atlas-dot-clear"/> No current file-scoped finding</span><span>{nodes.length} of {(analysis.architecture.nodes || []).length || analysis.files.length} displayed</span></div>
    </div>
    <section className="file-inspector">
      <div className="inspector-heading"><div><span className="section-index">FILE INTELLIGENCE</span><h3>{activePath || 'Select a file'}</h3></div><span className={`severity-chip ${activeHigh ? 'severity-chip-high' : activeFindings.length ? 'severity-chip-medium' : 'severity-chip-clear'}`}>{activeHigh ? `${activeHigh} HIGH / CRITICAL` : activeFindings.length ? `${activeFindings.length} SIGNAL${activeFindings.length === 1 ? '' : 'S'}` : 'NO CURRENT SIGNAL'}</span></div>
      <div className="inspector-stats">
        <div><span>Language</span><strong>{activeFile?.language || nodes.find(node => node.id === activePath)?.language || 'Unknown'}</strong></div>
        <div><span>Non-comment lines</span><strong>{activeFile ? activeFile.loc.toLocaleString() : '—'}</strong></div>
        <div><span>Physical lines</span><strong>{activeFile ? activeFile.lines.toLocaleString() : '—'}</strong></div>
        <div><span>File size</span><strong>{activeFile ? `${(activeFile.bytes / 1024).toFixed(1)} KB` : '—'}</strong></div>
      </div>
      {activeFindings.length ? <div className="inspector-findings">{activeFindings.slice(0, 4).map(finding => <article className="inspector-finding" key={finding.id}><span className={`risk-marker risk-${finding.severity.toLowerCase()}`}>{finding.severity}</span><div><strong>{finding.title}</strong><p>{finding.path}{finding.line_start ? `:${finding.line_start}` : ''} · {finding.description}</p></div></article>)}</div> : <p className="inspector-clear-note">The enabled checks did not attach a finding to this file. This is not a guarantee that the file is defect-free.</p>}
    </section>
  </div>;
}

function FindingsTable({ analysis, onUpdate }: { analysis: Analysis; onUpdate: (f: Finding, status: string) => void }) {
  const [filter,setFilter]=useState('ALL'); const [search,setSearch]=useState(''); const [expandedFinding,setExpandedFinding]=useState<string|null>(null);
  const filtered=useMemo(()=>analysis.findings.filter(f=>(filter==='ALL'||f.severity===filter)&&`${f.title} ${f.path} ${f.rule_id} ${f.id}`.toLowerCase().includes(search.toLowerCase())),[analysis,filter,search]);
  return <div className="findings-board"><div className="findings-toolbar"><div className="filter-pills"><button className={filter==='ALL'?'filter-active':''} onClick={()=>setFilter('ALL')}>All <span>{analysis.findings.length}</span></button>{SEVERITIES.map(s=><button key={s} className={filter===s?'filter-active':''} onClick={()=>setFilter(s)}>{s}</button>)}</div><input className="text-input search-input" value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search findings or file…" aria-label="Search findings"/></div>
    {!filtered.length ? <div className="empty-panel"><span className="empty-mark">✓</span><h3>No findings match this view</h3><p>Change the severity filter or search term to see other results.</p></div> : <div className="findings-list">{filtered.map(f=><article className="finding-card" key={f.id}><div className="finding-status-rail" style={{background:SEVERITY_COLOURS[f.severity]}}/><div className="finding-body"><div className="finding-title-row"><div><div className="finding-kicker">{f.rule_id} <span>·</span> {f.id}</div><h3>{f.title}</h3></div><SeverityPill severity={f.severity}/></div><p>{f.description}</p><div className="finding-preview-location"><AppIcon name="file" size={15}/><span>{f.path || 'Repository level'}{f.line_start ? `:${f.line_start}` : ''}</span><button type="button" className="finding-detail-trigger" aria-expanded={expandedFinding===f.id} aria-controls={`finding-detail-${f.id}`} onClick={() => setExpandedFinding(current => current===f.id ? null : f.id)}>{expandedFinding===f.id ? 'Hide details' : 'View evidence & fix'} <AppIcon name={expandedFinding===f.id ? 'chevron-down' : 'arrow-up-right'} size={14}/></button></div>{expandedFinding===f.id && <div className="finding-detail-expand" id={`finding-detail-${f.id}`}><div className="finding-evidence"><div><span className="code-file">{f.path || 'Repository level'}{f.line_start ? ` : ${f.line_start}` : ''}</span><code>{f.evidence || 'No source-line evidence; repository-level check.'}</code></div></div><div className="finding-remediation"><strong>Suggested remediation</strong><span>{f.remediation}</span></div><div className="finding-footer"><span className="confidence">{Math.round(f.confidence*100)}% confidence · {f.verification}</span><label className="status-select-label">Review status <select value={f.status||'open'} onChange={e=>onUpdate(f,e.target.value)} aria-label={`Set review status for ${f.id}`}><option value="open">Open</option><option value="investigate">Investigate</option><option value="accepted">Accepted</option><option value="fixed">Fixed</option><option value="ignored">Ignored</option></select></label></div></div>}</div></article>)}</div>}</div>;
}

type DownloadActionProps = { onDownload: () => Promise<boolean>; disabled?: boolean; label?: string; compact?: boolean };

function DownloadActionButton({ onDownload, disabled = false, label = 'Download PDF', compact = false }: DownloadActionProps) {
  const [state, setState] = useState<'idle' | 'preparing' | 'done'>('idle');
  const activate = async () => {
    if (disabled || state === 'preparing') return;
    setState('preparing');
    try {
      const ok = await onDownload();
      if (!ok) { setState('idle'); return; }
      setState('done');
      window.setTimeout(() => setState('idle'), 1800);
    } catch {
      setState('idle');
    }
  };
  const caption = state === 'preparing' ? 'Preparing…' : state === 'done' ? 'Downloaded' : label;
  return <button type="button" className={`btn btn-primary btn-pill download-action ${compact ? 'download-action-compact' : ''} download-${state}`} onClick={() => void activate()} disabled={disabled || state === 'preparing'} aria-live="polite">
    <span className="download-action-icon" aria-hidden="true">{state === 'done' ? '✓' : state === 'preparing' ? '◌' : '↓'}</span>
    <span>{caption}</span>
    <i className="download-progress-line" aria-hidden="true" />
  </button>;
}

function ShareSummaryControl({ analysis, job }: { analysis: Analysis; job: AnalysisJob }) {
  const [open, setOpen] = useState(false);
  const [feedback, setFeedback] = useState('');
  const summaryText = `${analysis.project} — Sentinal analysis snapshot\nHealth triage: ${analysis.summary.health_score}/100\nFiles analyzed: ${analysis.summary.files_analyzed}\nSource lines: ${analysis.summary.source_lines}\nFindings: ${analysis.summary.findings_total}\nSnapshot ID: ${job.id}\n\nEvidence-based static analysis. Findings should be reviewed by a human; a pattern match is not proof of exploitability.`;
  const copyText = async (text: string, doneMessage: string) => {
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard is unavailable in this browser context.');
      await navigator.clipboard.writeText(text);
      setFeedback(doneMessage);
    } catch (error) {
      setFeedback(error instanceof Error ? error.message : 'Could not copy this text.');
    }
  };
  const shareSummary = async () => {
    try {
      if (navigator.share) {
        await navigator.share({ title: `${analysis.project} — Sentinal report`, text: summaryText });
        setFeedback('Share sheet opened.');
      } else {
        await copyText(summaryText, 'Summary copied to clipboard.');
      }
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') return;
      await copyText(summaryText, 'Summary copied to clipboard.');
    }
  };
  return <div className={`share-summary ${open ? 'share-summary-open' : ''}`}>
    <button type="button" className="btn btn-outline btn-pill share-summary-trigger" onClick={() => { setOpen(v => !v); setFeedback(''); }} aria-expanded={open}><span>↗</span> Share summary</button>
    {open && <div className="share-summary-menu" role="group" aria-label="Share or copy report summary">
      <button type="button" onClick={() => void shareSummary()}><span>↗</span><span><strong>Share summary</strong><small>Open your device share sheet</small></span></button>
      <button type="button" onClick={() => void copyText(summaryText, 'Summary copied to clipboard.')}><span>⧉</span><span><strong>Copy summary</strong><small>Metrics and review caveat</small></span></button>
      <button type="button" onClick={() => void copyText(job.id, 'Snapshot ID copied to clipboard.')}><span>#</span><span><strong>Copy snapshot ID</strong><small>{job.id}</small></span></button>
      {feedback && <p role="status">{feedback}</p>}
    </div>}
  </div>;
}

function ReportPreview({ analysis, job, onDownload, onNavigate }: { analysis: Analysis; job: AnalysisJob; onDownload: () => Promise<boolean>; onNavigate: (page: Page) => void }) {
  const [previewPage, setPreviewPage] = useState(0);
  const pages = [
    { title: 'Executive snapshot', subtitle: 'A measured overview of this source tree' },
    { title: 'Priority findings', subtitle: 'Evidence-linked items for human review' },
    { title: 'Source coverage', subtitle: 'Detected languages and repository inventory' },
  ];
  const highCount = (analysis.severity_counts.CRITICAL || 0) + (analysis.severity_counts.HIGH || 0);
  const topFindings = [...analysis.findings].sort((a, b) => {
    const rank: Record<Severity, number> = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3, INFO: 4 };
    return rank[a.severity] - rank[b.severity];
  }).slice(0, 4);
  return <section className="panel report-preview-panel">
    <div className="panel-head report-preview-heading"><div><span className="section-index">DOCUMENT STUDIO / 06</span><h2>Report preview</h2><p className="panel-subhead">A quick, readable preview of the real analysis report.</p></div><span className="panel-tag">{job.status === 'completed' ? 'PDF READY' : 'REPORT PENDING'}</span></div>
    <div className="report-studio">
      <div className="receipt-stage">
        <div className="printer-top" aria-hidden="true"><span /><span /></div>
        <article className={`report-paper report-paper-page-${previewPage}`} key={previewPage} aria-label={`Report preview section ${previewPage + 1}`}>
          <div className="paper-brand-strip"><span className="paper-brand-mark">S.</span><span>SENTINAL / CODEBASE INTELLIGENCE</span><span className="paper-page-number">SECTION 0{previewPage + 1}</span></div>
          <div className="paper-rule" />
          <p className="paper-eyebrow">{pages[previewPage].title.toUpperCase()}</p>
          <h3>{analysis.project}</h3>
          <p className="paper-subtitle">{pages[previewPage].subtitle}</p>
          {previewPage === 0 && <>
            <div className="paper-orange-banner"><span>HEURISTIC HEALTH TRIAGE</span><strong>{analysis.summary.health_score}<small> / 100</small></strong><div className="paper-health-track"><i style={{ width: `${Math.max(0, Math.min(100, analysis.summary.health_score))}%` }} /></div><small>Directional score · not a certification</small></div>
            <div className="paper-stat-grid"><div><span>FILES</span><strong>{analysis.summary.files_analyzed.toLocaleString()}</strong></div><div><span>FINDINGS</span><strong>{analysis.summary.findings_total.toLocaleString()}</strong></div><div><span>SOURCE LINES</span><strong>{analysis.summary.source_lines.toLocaleString()}</strong></div></div>
            <div className="paper-section-label">RISK AT A GLANCE</div>
            <div className="paper-severity-row"><span className="paper-sev sev-critical-dot" />Critical <strong>{analysis.severity_counts.CRITICAL || 0}</strong></div>
            <div className="paper-severity-row"><span className="paper-sev sev-high-dot" />High <strong>{analysis.severity_counts.HIGH || 0}</strong></div>
            <div className="paper-severity-row"><span className="paper-sev sev-medium-dot" />Medium <strong>{analysis.severity_counts.MEDIUM || 0}</strong></div>
            <div className="paper-evidence-note">{highCount ? `${highCount} high/critical signal${highCount === 1 ? '' : 's'} should be reviewed first.` : 'No high or critical findings were returned by the enabled checks.'}</div>
          </>}
          {previewPage === 1 && <>
            <div className="paper-section-label">REVIEW FIRST</div>
            {topFindings.length ? topFindings.map((finding, index) => <div className="paper-finding" key={finding.id}><div className="paper-finding-top"><span>0{index + 1} / {finding.rule_id}</span><b className={`paper-risk paper-risk-${finding.severity.toLowerCase()}`}>{finding.severity}</b></div><strong>{finding.title}</strong><code>{finding.path || 'Repository level'}{finding.line_start ? `:${finding.line_start}` : ''}</code><p>{finding.remediation}</p></div>) : <div className="paper-evidence-note">No findings were returned by the enabled checks. This is not proof that the code is defect-free.</div>}
          </>}
          {previewPage === 2 && <>
            <div className="paper-section-label">LANGUAGE COVERAGE</div>
            {analysis.languages.slice(0, 7).map((language, index) => <div className="paper-language-row" key={language.name}><span className={`paper-language-dot paper-language-${index % 5}`} /><span>{language.name}</span><strong>{language.loc.toLocaleString()} LOC</strong><div className="paper-language-track"><i style={{ width: `${analysis.summary.source_lines ? Math.max(2, language.loc / analysis.summary.source_lines * 100) : 0}%` }} /></div></div>)}
            <div className="paper-section-label">SCOPE NOTE</div><p className="paper-scope-note">{analysis.architecture.scope_note || 'The map contains statically inferred relationships. Dynamic loading and runtime-only relationships may not be represented.'}</p>
            <div className="paper-evidence-note">Evidence and remediation are leads for review, not proof of exploitability or correctness.</div>
          </>}
          <div className="paper-footer"><span>LOCAL-FIRST · EVIDENCE-LED</span><span>{new Date(job.completed_at || job.created_at || Date.now()).toLocaleDateString()}</span></div>
        </article>
      </div>
      <div className="report-preview-controls">
        <div className="preview-pager"><button type="button" onClick={() => setPreviewPage((previewPage + pages.length - 1) % pages.length)} aria-label="Previous preview section">←</button><span><strong>SECTION 0{previewPage + 1}</strong> / 03 <small>{pages[previewPage].title}</small></span><button type="button" onClick={() => setPreviewPage((previewPage + 1) % pages.length)} aria-label="Next preview section">→</button></div>
        <div className="preview-actions"><button type="button" className="btn btn-outline btn-pill" onClick={() => onNavigate('Findings')}>Review findings <span>↗</span></button><ShareSummaryControl analysis={analysis} job={job}/><DownloadActionButton onDownload={onDownload} disabled={job.status !== 'completed'} compact /></div>
        <p className="preview-disclaimer">This summary has three interactive sections; the downloaded report is composed as four full PDF pages.</p>
      </div>
    </div>
  </section>;
}

function FloatingDock({ page, onNavigate, canDownload, onDownload }: { page: Page; onNavigate: (page: Page) => void; canDownload: boolean; onDownload: () => Promise<boolean> }) {
  const [expanded, setExpanded] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);
  const moreButtonRef = useRef<HTMLButtonElement | null>(null);
  const mobileMoreItems = NAV_ITEMS.filter(item => !MOBILE_PRIMARY_NAV.has(item.label));
  const isSecondaryPage = mobileMoreItems.some(item => item.label === page);
  useEffect(() => {
    if (!moreOpen) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setMoreOpen(false);
        moreButtonRef.current?.focus();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [moreOpen]);
  const navigate = (destination: Page) => {
    onNavigate(destination);
    setMoreOpen(false);
    setExpanded(false);
  };
  return <nav className={`floating-dock ${expanded ? 'floating-dock-expanded' : ''}`} aria-label="Primary navigation" onMouseEnter={() => { if (window.matchMedia('(pointer: fine)').matches) setExpanded(true); }} onMouseLeave={() => setExpanded(false)} onFocusCapture={() => setExpanded(true)} onBlurCapture={(event) => { if (!event.currentTarget.contains(event.relatedTarget as Node | null)) { setExpanded(false); setMoreOpen(false); } }}>
    <span className="dock-logo" aria-hidden="true">S<span>.</span></span>
    {NAV_ITEMS.map(item => <button type="button" key={item.label} className={`dock-item ${MOBILE_PRIMARY_NAV.has(item.label) ? 'dock-item-mobile-primary' : 'dock-item-mobile-secondary'} ${page === item.label ? 'dock-item-active' : ''}`} onClick={() => navigate(item.label)} aria-label={item.label} aria-current={page === item.label ? 'page' : undefined} title={item.note}><span className="dock-symbol" aria-hidden="true"><AppIcon name={item.icon} size={20}/></span><span className="dock-label">{item.label}</span></button>)}
    <span className="dock-divider" aria-hidden="true"/>
    <button type="button" className="dock-item dock-pdf-item" disabled={!canDownload} onClick={() => { void onDownload(); setExpanded(false); }} aria-label="Download PDF report" title={canDownload ? 'Download PDF report' : 'Complete an analysis to enable the PDF report'}><span className="dock-symbol" aria-hidden="true"><AppIcon name="download" size={20}/></span><span className="dock-label">PDF report</span></button>
    <button ref={moreButtonRef} type="button" className={`dock-mobile-more ${moreOpen || isSecondaryPage ? 'dock-mobile-more-active' : ''}`} aria-haspopup="true" aria-expanded={moreOpen} aria-controls="dock-more-menu" aria-current={isSecondaryPage ? 'page' : undefined} aria-label={moreOpen ? 'Close more destinations' : 'More destinations'} onClick={() => setMoreOpen(open => !open)}><span className="dock-symbol" aria-hidden="true"><AppIcon name={moreOpen ? 'x' : 'more-horizontal'} size={20}/></span><span className="dock-label">More</span></button>
    <button type="button" className="dock-toggle" onClick={() => setExpanded(v => !v)} aria-expanded={expanded} aria-label={expanded ? 'Collapse navigation dock' : 'Expand navigation dock'}><AppIcon name={expanded ? 'x' : 'chevron-down'} size={17}/></button>
    {moreOpen && <div className="dock-more-menu" id="dock-more-menu" role="group" aria-label="More destinations">
      {mobileMoreItems.map(item => <button type="button" key={item.label} className={`dock-more-action ${page === item.label ? 'dock-more-action-active' : ''}`} onClick={() => navigate(item.label)} aria-current={page === item.label ? 'page' : undefined}>
        <span className="dock-more-icon"><AppIcon name={item.icon} size={18}/></span><span>{item.label}</span><small>{item.note}</small>
      </button>)}
      <span className="dock-more-divider" aria-hidden="true"/>
      <button type="button" className="dock-more-action" disabled={!canDownload} onClick={() => { void onDownload(); setMoreOpen(false); }} aria-label="Download PDF report">
        <span className="dock-more-icon"><AppIcon name="download" size={18}/></span><span>PDF report</span><small>{canDownload ? 'Download completed analysis' : 'Available after an analysis'}</small>
      </button>
    </div>}
  </nav>;
}

function WorkflowPanel({ job, onNew, onNavigate, onDownload }: { job: AnalysisJob | null; onNew: () => void; onNavigate: (page: Page) => void; onDownload: () => Promise<boolean> }) {
  const stages = [
    { title: 'Repository', detail: 'Connect source', icon: 'git-branch' },
    { title: 'Analyze', detail: 'Inspect files', icon: 'scan' },
    { title: 'Understand', detail: 'Map structure', icon: 'network' },
    { title: 'Prove', detail: 'Trace evidence', icon: 'shield' },
    { title: 'Review', detail: 'Prioritize issues', icon: 'check' },
    { title: 'Actionable insights', detail: 'Export report', icon: 'arrow-up-right' },
  ];
  const status = job?.status || 'idle';
  const completed = status === 'completed';
  const activeIndex = status === 'analyzing' ? 1 : status === 'explaining' ? 3 : status === 'reporting' ? 5 : completed ? 5 : job ? 1 : 0;
  const isDone = (index: number) => completed
    || (status === 'analyzing' && index < 1)
    || (status === 'explaining' && index < 3)
    || (status === 'reporting' && index < 5);
  const activateStage = (index: number) => {
    if (index <= 1) onNew();
    else if (index === 2) onNavigate('Architecture');
    else if (index === 3 || index === 4) onNavigate('Findings');
    else if (index === 5 && completed) void onDownload();
    else onNew();
  };

  return <section className="panel workflow-panel" aria-label="Sentinal analysis workflow">
    <div className="workflow-heading">
      <div>
        <span className="section-index">FROM SOURCE TO SIGNAL</span>
        <h2>How Sentinal builds understanding</h2>
        <p>Evidence moves from repository inventory to an actionable review. Each finding points back to code.</p>
      </div>
      <span className={`workflow-status ${completed ? 'workflow-status-complete' : job && status !== 'failed' ? 'workflow-status-running' : ''}`}>
        <i />{completed ? 'Snapshot complete' : status === 'failed' ? 'Analysis failed' : job ? status.replace('-', ' ') : 'Ready to analyze'}
      </span>
    </div>
    <div className="workflow-track">
      {stages.map((stage, index) => <Fragment key={stage.title}>
        {index > 0 && <span className={`workflow-connector ${isDone(index - 1) ? 'workflow-connector-done' : job && status !== 'failed' && index - 1 === activeIndex ? 'workflow-connector-active' : ''}`} aria-hidden="true"><i /></span>}
        <button type="button" data-stage={index} className={`workflow-step ${isDone(index) ? 'workflow-step-done' : ''} ${!completed && status !== 'failed' && index === activeIndex ? 'workflow-step-active' : ''}`} onClick={() => activateStage(index)} title={index < 2 ? 'Start a repository analysis' : index === 5 && completed ? 'Download the generated report' : `Open ${stage.title.toLowerCase()} view`}>
          <span className="workflow-step-icon"><AppIcon name={stage.icon} size={19}/>{isDone(index) && <i><AppIcon name="check" size={10}/></i>}</span>
          <strong>{stage.title}</strong>
          <small>{stage.detail}</small>
        </button>
      </Fragment>)}
    </div>
    <div className="workflow-foot">
      <span><AppIcon name="lock" size={14}/> Submitted application code is not executed during a normal scan.</span>
      <button type="button" className="text-action" onClick={onNew}>{job ? 'Analyze another repository' : 'Analyze a repository'} <AppIcon name="arrow-up-right" size={15}/></button>
    </div>
  </section>;
}

const PRODUCT_TOUR_STEPS = [
  {
    eyebrow: '01 / MAP THE REPOSITORY',
    title: 'Start with the code that is actually there.',
    body: 'Submit a public GitHub repository or a source ZIP. Sentinal inventories supported files and maps static relationships without executing the submitted application.',
  },
  {
    eyebrow: '02 / FOLLOW THE EVIDENCE',
    title: 'Every signal points back to a file.',
    body: 'Review severity, rule ID, source location, match confidence, and the recommended verification step. Triage each item in the same analysis snapshot.',
  },
  {
    eyebrow: '03 / SHARE THE DECISION',
    title: 'Turn the review into a four-page brief.',
    body: 'Export repository shape, severity charts, prioritized remediation, and coverage notes as a printable engineering report.',
  },
] as const;

function ProductTour({ onClose, onStart }: { onClose: () => void; onStart: () => void }) {
  const [step, setStep] = useState(0);
  const [playing, setPlaying] = useState(false);
  const dialogRef = useRef<HTMLElement | null>(null);
  const current = PRODUCT_TOUR_STEPS[step];

  useEffect(() => {
    if (!playing) return;
    const timer = window.setInterval(() => setStep(value => (value + 1) % PRODUCT_TOUR_STEPS.length), 4600);
    return () => window.clearInterval(timer);
  }, [playing]);

  useEffect(() => {
    const previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const focusableButtons = () => Array.from(dialogRef.current?.querySelectorAll<HTMLButtonElement>('button:not(:disabled)') || []);
    focusableButtons()[0]?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
      if (event.key === 'ArrowRight') setStep(value => Math.min(value + 1, PRODUCT_TOUR_STEPS.length - 1));
      if (event.key === 'ArrowLeft') setStep(value => Math.max(value - 1, 0));
      if (event.key === 'Tab') {
        const buttons = focusableButtons();
        if (!buttons.length) return;
        if (event.shiftKey && document.activeElement === buttons[0]) {
          event.preventDefault();
          buttons[buttons.length - 1].focus();
        } else if (!event.shiftKey && document.activeElement === buttons[buttons.length - 1]) {
          event.preventDefault();
          buttons[0].focus();
        }
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => {
      window.removeEventListener('keydown', onKeyDown);
      document.body.style.overflow = previousOverflow;
      previousFocus?.focus();
    };
  }, [onClose]);

  const next = () => {
    if (step === PRODUCT_TOUR_STEPS.length - 1) {
      setPlaying(false);
      onClose();
      onStart();
      return;
    }
    setStep(value => value + 1);
  };

  return createPortal(<div className="tour-backdrop" onMouseDown={event => { if (event.target === event.currentTarget) onClose(); }}>
    <section ref={dialogRef} className="tour-dialog" role="dialog" aria-modal="true" aria-labelledby="tour-title" aria-describedby="tour-description" tabIndex={-1}>
      <div className={`tour-stage tour-stage-${step + 1}`} aria-hidden="true">
        <div className="tour-stage-kicker"><span>ILLUSTRATIVE UI / NOT SCAN DATA</span><b>0{step + 1}</b></div>
        <div className="tour-blueprint-grid"/>
        {step === 0 ? <div className="tour-repository-art">
          <div className="tour-root-node"><AppIcon name="code" size={17}/><span>project tree</span><b>inventory</b></div>
          <div className="tour-tree-branch tour-branch-one"/><div className="tour-tree-branch tour-branch-two"/>
          <div className="tour-file-node node-python"><span className="tour-node-dot"/>source path</div>
          <div className="tour-file-node node-typescript"><span className="tour-node-dot"/>module link</div>
          <div className="tour-file-node node-config"><span className="tour-node-dot"/>file inventory</div>
          <div className="tour-orbit-label">STATIC IMPORT MAP</div>
          <div className="tour-halftone"/>
        </div> : step === 1 ? <div className="tour-evidence-art">
          <div className="tour-evidence-top"><span>EXAMPLE FINDING / RULE SIGNAL</span><b className="tour-severity-high">HIGH</b></div>
          <strong>Evidence linked to a source path</strong>
          <div className="tour-code-lines"><i/><i/><i/><i/></div>
          <div className="tour-evidence-meta"><span>REPORTED SOURCE LOCATION</span><b>MATCH CONFIDENCE</b></div>
          <div className="tour-evidence-action"><AppIcon name="check" size={15}/> Verify surrounding input</div>
        </div> : <div className="tour-report-art">
          <div className="tour-report-head"><span>SENTINAL</span><b>CODEBASE REVIEW</b></div>
          <div className="tour-report-title-lines"><i/><i/></div>
          <div className="tour-report-metrics"><i/><i/><i/></div>
          <div className="tour-report-chart"><div className="tour-report-donut"/><div className="tour-report-bars"><i/><i/><i/><i/></div></div>
          <div className="tour-report-footer">ENGINEERING INTELLIGENCE / 04 PAGES</div>
        </div>}
      </div>
      <div className="tour-content">
        <div className="tour-topline"><span>INTERACTIVE PRODUCT TOUR</span><button type="button" className="tour-close" onClick={onClose} aria-label="Close product tour"><AppIcon name="x" size={18}/></button></div>
        <div className="tour-copy" aria-live="polite">
          <span className="tour-step-label">{current.eyebrow}</span>
          <h2 id="tour-title">{current.title}</h2>
          <p id="tour-description">{current.body}</p>
        </div>
        <div className="tour-progress" role="progressbar" aria-label="Product tour progress" aria-valuemin={1} aria-valuemax={PRODUCT_TOUR_STEPS.length} aria-valuenow={step + 1}>
          <span style={{ width: `${((step + 1) / PRODUCT_TOUR_STEPS.length) * 100}%` }}/>
        </div>
        <div className="tour-controls">
          <button type="button" className="tour-previous" onClick={() => setStep(value => Math.max(value - 1, 0))} disabled={step === 0}>Previous</button>
          <div className="tour-control-group">
            <button type="button" className="tour-play" onClick={() => setPlaying(value => !value)}>{playing ? 'Pause tour' : 'Play tour'}</button>
            <button type="button" className="btn btn-primary btn-pill tour-next" onClick={next}>{step === PRODUCT_TOUR_STEPS.length - 1 ? 'Start a review' : 'Next step'} <AppIcon name="arrow-up-right" size={15}/></button>
          </div>
        </div>
        <span className="tour-key-hint">Use left and right arrow keys to move between steps.</span>
      </div>
    </section>
  </div>, document.body);
}

function Home({ job, busy, onNew, onDownload, onNavigate, history, onOpenHistory }: {
  job: AnalysisJob | null; busy: boolean; onNew: () => void; onDownload: () => Promise<boolean>;
  onNavigate: (page: Page) => void; history: Record<string, unknown>[]; onOpenHistory: (id: string) => void;
}) {
  const analysis = job?.analysis; const summary = analysis?.summary; const ai = job?.ai_summary;
  const recent = analysis?.findings.slice(0, 4) || [];
  const completedHistory = history.filter(item => item.status === 'completed').slice(0, 4);
  const repoLabel = analysis?.source.repository_url || analysis?.source.filename || 'Uploaded project';
  const highCount = (analysis?.severity_counts.CRITICAL || 0) + (analysis?.severity_counts.HIGH || 0);
  const [tourOpen, setTourOpen] = useState(false);
  return <div className="page-stack home-stack">
    <section className="welcome-row"><div><div className="eyebrow"><span className="eyebrow-dot"/> CODEBASE INTELLIGENCE / WORKSPACE</div><h1>{analysis ? <>Review with <em>precision.</em></> : <>Understand Your Code. <em>Prove Every Decision.</em></>}</h1><p className="subtitle">{analysis ? `A measured snapshot of ${analysis.project}, its code structure, and the signals worth reviewing.` : 'Transform complex repositories into understandable architecture, traceable execution flows, and actionable code intelligence.'}</p></div><div className="home-header-actions"><button className="btn btn-outline btn-pill" onClick={() => setTourOpen(true)}>Take product tour <AppIcon name="play" size={15}/></button>{analysis && <button className="btn btn-primary btn-pill" onClick={onNew}>New analysis <AppIcon name="arrow-up-right" size={16}/></button>}</div></section>
    {job && <WorkflowPanel job={job} onNew={onNew} onNavigate={onNavigate} onDownload={onDownload}/>}
    {busy && job && <section className="pipeline-banner"><div className="mini-loader"><span/><span/><span/><span/></div><div className="pipeline-copy"><strong>{job.status === 'analyzing' ? 'Inspecting source files' : job.status === 'explaining' ? 'Generating the evidence explanation' : job.status === 'reporting' ? 'Composing your four-page report' : 'Preparing analysis'}</strong><span>{job.project} · {job.progress || 0}% complete{job.status === 'explaining' ? ' · Local model work may take a little longer on larger scans.' : ''}</span><div className="progress-track"><span style={{width:`${job.progress || 0}%`}}/></div></div><span className="progress-number">{job.progress || 0}%</span></section>}
    {job?.status === 'failed' && <div className="notice notice-error">{job.error || 'Analysis failed. Check the input and try again.'}</div>}
    {!analysis ? <>
      <section className="welcome-hero">
        <div className="welcome-hero-copy"><span className="hero-chip"><i/> LOCAL-FIRST · EVIDENCE-LED</span><h2>Your next code review, <span>without the guesswork.</span></h2><p>Sentinal maps the code you submitted, connects findings to files, and turns the results into a short report you can actually present.</p><div className="hero-actions"><button className="btn btn-primary btn-pill" onClick={onNew}>Start a codebase review <AppIcon name="arrow-up-right" size={17}/></button></div><div className="hero-assurances"><span>✓ No source execution</span><span>✓ File-level evidence</span><span>✓ Compact PDF</span></div></div>
        <div className="hero-visual" aria-hidden="true"><div className="orbit orbit-one"/><div className="orbit orbit-two"/><div className="hero-glyph"><span className="glyph-tile glyph-blue">{ }</span><span className="glyph-tile glyph-orange">!</span><span className="glyph-tile glyph-lime">✓</span><span className="glyph-tile glyph-violet">⌘</span></div><div className="floating-label floating-label-top">STATIC ANALYSIS <b>01</b></div><div className="floating-label floating-label-bottom">SIGNALS → ACTION <b>02</b></div><span className="hero-spark spark-one">✳</span><span className="hero-spark spark-two">+</span></div>
      </section>
      <section className="capability-grid">
        <TiltSurface className="capability-card capability-blue"><span className="capability-index">01 / INVENTORY</span><div className="capability-icon"><AppIcon name="file" size={23}/></div><h3>Know what's inside</h3><p>Languages, file sizes, functions, test hints, dependencies, and source layout in one snapshot.</p></TiltSurface>
        <TiltSurface className="capability-card capability-orange"><span className="capability-index">02 / REVIEW</span><div className="capability-icon"><AppIcon name="shield" size={23}/></div><h3>Trace every signal</h3><p>Review rule IDs, relevant lines, confidence, and a practical remediation suggestion.</p></TiltSurface>
        <TiltSurface className="capability-card capability-violet"><span className="capability-index">03 / EXPLAIN</span><div className="capability-icon"><AppIcon name="sparkles" size={23}/></div><h3>Ask your local model</h3><p>Use Ollama for concise explanations grounded in the selected analysis, not general guesswork.</p><button className="text-action" onClick={() => onNavigate('Ask Sentinal')}>Open Ask Sentinal ↗</button></TiltSurface>
      </section>
      <section className="panel recent-panel"><div className="panel-head"><div><span className="section-index">RECENT ACTIVITY</span><h2>Pick up where you left off</h2></div><button className="btn btn-outline btn-pill" onClick={() => onNavigate('History')}>View history ↗</button></div>{completedHistory.length ? <div className="recent-run-list">{completedHistory.map((item, index) => <button className="recent-run" key={String(item.id || index)} onClick={() => item.id && onOpenHistory(String(item.id))}><span className="run-index">0{index + 1}</span><span className="run-main"><strong>{String(item.project || 'Codebase analysis')}</strong><small>{String(item.source && typeof item.source === 'object' ? (item.source as Record<string, unknown>).repository_url || (item.source as Record<string, unknown>).filename || 'Uploaded source' : 'Saved analysis')}</small></span><span className={`job-status status-${String(item.status || 'queued')}`}>{String(item.status || 'queued')}</span><span className="row-arrow">↗</span></button>)}</div> : <div className="empty-activity"><div className="empty-activity-icon">&#9671;</div><div><strong>No completed scans yet.</strong><p>Completed analyses will appear here. The main action above accepts a public GitHub repository or a source ZIP.</p></div></div>}</section>
    </> : <>
      <section className="analysis-context"><div className="analysis-context-mark">S<span>.</span></div><div className="analysis-context-main"><span className="section-index">CURRENT SNAPSHOT</span><h2>{analysis.project}</h2><p>{repoLabel} <span>·</span> {analysis.source.branch || 'uploaded archive'} <span>·</span> {job?.completed_at ? new Date(job.completed_at).toLocaleString() : 'Saved analysis'}</p></div><div className="context-actions"><button className="btn btn-outline btn-pill" onClick={() => onNavigate('Architecture')}>Explore Repo Atlas ↗</button><DownloadActionButton onDownload={onDownload} disabled={busy || job?.status !== 'completed'} label="Download report" /></div></section>
      <section className="metrics-grid"><MetricCard label="Health triage" value={`${summary?.health_score ?? '—'}/100`} caption="Heuristic · not a certification" icon="shield" tone="orange"/><MetricCard label="Files analyzed" value={(summary?.files_analyzed ?? 0).toLocaleString()} caption={`${analysis.languages.length} language groups`} icon="file"/><MetricCard label="Source lines" value={(summary?.source_lines ?? 0).toLocaleString()} caption="Non-comment, non-blank estimate" icon="code" tone="navy"/><MetricCard label="Findings" value={(summary?.findings_total ?? analysis.findings.length).toLocaleString()} caption={`${highCount} high / critical signals`} icon="scan" tone="violet"/></section>
      <section className="dashboard-grid dashboard-grid-top"><article className="panel chart-panel"><div className="panel-head"><div><span className="section-index">COMPOSITION / 01</span><h2>Where the code lives</h2><p className="panel-subhead">Lines of code by detected language</p></div><span className="panel-number">01</span></div><LanguageChart analysis={analysis}/><div className="panel-footnote">Line counts are approximate and exclude common comment markers.</div></article><article className="panel chart-panel"><div className="panel-head"><div><span className="section-index">RISK PROFILE / 02</span><h2>Signals by severity</h2><p className="panel-subhead">Rule-based indicators for human review</p></div><span className="panel-number panel-number-coral">02</span></div><SeverityDonut analysis={analysis}/><div className="panel-footnote">A pattern match is a lead to review—not proof of exploitability.</div></article></section>
      <section className="dashboard-grid dashboard-grid-bottom"><article className="panel chart-panel"><div className="panel-head"><div><span className="section-index">FILE WEIGHT / 03</span><h2>Largest source units</h2><p className="panel-subhead">Prioritize complexity and file size</p></div><button className="btn btn-quiet btn-pill" onClick={() => onNavigate('Architecture')}>All files ↗</button></div><FileBarChart analysis={analysis}/></article><article className="panel summary-panel"><div className="panel-head"><div><span className="section-index">REVIEW BRIEF / 04</span><h2>The useful takeaway</h2></div><span className={`mode-label ${ai?.mode?.toLowerCase().includes('ai') ? 'mode-ai' : ''}`}>{ai?.mode || 'Evidence-only'}</span></div><p className="executive-summary">{ai?.executive_summary || 'The structured analysis is available. This scan did not produce a narrative explanation.'}</p><div className="summary-meta"><span>{repoLabel}</span><span>·</span><span>{analysis.source.branch || 'archive'}</span></div><div className="summary-actions"><button className="btn btn-outline btn-pill" onClick={() => onNavigate('Findings')}>Review findings <span>→</span></button><button className="btn btn-primary btn-pill" onClick={() => onNavigate('Ask Sentinal')}>Ask Sentinal <span>✳</span></button></div></article></section>
      <ReportPreview analysis={analysis} job={job!} onDownload={onDownload} onNavigate={onNavigate}/>
      <section className="priority-section"><div className="section-title-row"><div><span className="section-index">PRIORITY QUEUE / 05</span><h2>Start with what matters</h2><p>Highest-priority signals from this saved snapshot.</p></div><button className="btn btn-outline btn-pill" onClick={() => onNavigate('Findings')}>View all findings ↗</button></div>{recent.length === 0 ? <div className="panel no-findings-note"><span>✓</span><div><strong>No findings reported by enabled checks.</strong><p>This is not a guarantee that the codebase is free of issues; review coverage and limits before release.</p></div></div> : <div className="priority-grid">{recent.map(finding => <button className="priority-card" key={finding.id} onClick={() => onNavigate('Findings')}><div className="priority-top"><span className={`risk-marker risk-${finding.severity.toLowerCase()}`}>{finding.severity}</span><span className="priority-rule">{finding.rule_id}</span></div><strong>{finding.title}</strong><p>{finding.description}</p><div className="priority-location"><span>{finding.path || 'Repository-level'}{finding.line_start ? `:${finding.line_start}` : ''}</span><span>Inspect ↗</span></div></button>)}</div>}</section>
    </>}
    {tourOpen && <ProductTour onClose={() => setTourOpen(false)} onStart={onNew}/>}
    <footer className="content-foot"><span>Sentinal / Evidence first.</span><span>{analysis ? `Snapshot ${job?.id || ''} · ${summary?.files_analyzed || 0} files measured` : 'Local-first code intelligence'}</span></footer>
  </div>;
}

function NewAnalysis({ onSubmitRepo, onSubmitFile, busy }: {onSubmitRepo:(data:{repository_url:string;branch:string;project_label:string;include_security:boolean;include_quality:boolean;include_architecture:boolean;audience:'mentor'|'developer'})=>void;onSubmitFile:(file:File,label:string,audience:'mentor'|'developer',options:{include_security:boolean;include_quality:boolean;include_architecture:boolean})=>void;busy:boolean}) {
  const [tab,setTab]=useState<'repo'|'zip'>('repo'); const [repo,setRepo]=useState('');const [branch,setBranch]=useState('main');const [label,setLabel]=useState('');const [audience,setAudience]=useState<'mentor'|'developer'>('developer');const [security,setSecurity]=useState(true);const [quality,setQuality]=useState(true);const [architecture,setArchitecture]=useState(true);const [file,setFile]=useState<File|null>(null);const [drag,setDrag]=useState(false);const [fileError,setFileError]=useState('');
  const selectFile=(f?:File)=>{if(!f)return;setFileError('');if(!f.name.toLowerCase().endsWith('.zip')){setFile(null);setFileError('Choose a ZIP archive. Other file types are not supported.');return;}if(f.size>5*1024*1024){setFile(null);setFileError('This ZIP is larger than the 5 MB limit. Choose a smaller archive.');return;}setFile(f)};
  return <div className="page-stack"><section className="page-title-row"><div><span className="eyebrow"><span className="eyebrow-dot"/> CODEBASE INTAKE</span><h1>Bring a codebase into focus.</h1><p className="subtitle">Choose how to submit the source; execution stays off by default.</p></div></section>
    <div className="intake-layout"><section className="panel intake-panel"><div className="panel-head"><div><span className="section-index">SOURCE</span><h2>Where is your project?</h2></div><span className="step-counter">STEP 01 / 03</span></div><div className="source-tabs"><button className={tab==='repo'?'source-tab-active':''} onClick={()=>setTab('repo')}><span>⑂</span> GitHub repository</button><button className={tab==='zip'?'source-tab-active':''} onClick={()=>setTab('zip')}><span>⇧</span> Upload ZIP</button></div>
      {tab==='repo'?<div className="source-form"><label className="field-label" htmlFor="repo-url">Repository URL</label><input id="repo-url" className="text-input" value={repo} onChange={e=>setRepo(e.target.value)} placeholder="https://github.com/owner/repository"/><div className="field-hint">Public repositories are supported in this build. Private repositories need an explicit OAuth/GitHub App authorization flow.</div><div className="form-two-col"><div><label className="field-label" htmlFor="repo-branch">Branch</label><input id="repo-branch" className="text-input" value={branch} onChange={e=>setBranch(e.target.value)} placeholder="main"/></div><div><label className="field-label" htmlFor="project-label">Project label <span className="optional">OPTIONAL</span></label><input id="project-label" className="text-input" value={label} onChange={e=>setLabel(e.target.value)} placeholder="e.g. Student portal"/></div></div><div className="helper-card"><span className="helper-icon">i</span><p>Sentinal inventories supported files and examines selected code patterns. It does not install dependencies or execute your application code.</p></div><button className="btn btn-primary full-button" disabled={busy||!repo.trim()} onClick={()=>onSubmitRepo({repository_url:repo.trim(),branch:branch.trim()||'main',project_label:label,include_security:security,include_quality:quality,include_architecture:architecture,audience})}>{busy?'Submitting…':'Analyze repository'} <span>↗</span></button></div>:<div className={`drop-zone ${drag?'drop-zone-active':''}`} onDragOver={e=>{e.preventDefault();setDrag(true)}} onDragLeave={e=>{if(e.currentTarget.contains(e.relatedTarget as Node|null))return;setDrag(false)}} onDrop={e=>{e.preventDefault();setDrag(false);selectFile(e.dataTransfer.files?.[0])}}><input id="zip-file" type="file" accept=".zip,application/zip" onChange={e=>selectFile(e.target.files?.[0])}/><label htmlFor="zip-file" className="drop-zone-content"><span className="upload-art" aria-hidden="true"><i>▧</i><i>♫</i><i>▤</i></span><strong>{file?'ZIP selected':'Drop a ZIP archive here'}</strong><span>{file?'You can replace this file or continue below':'or browse from your computer'}</span><em>ZIP only · 5 MB maximum · source/text files only</em></label>{fileError&&<div className="notice notice-error upload-error" role="alert">{fileError}</div>}{file&&<div className="selected-file-card"><span className="selected-file-icon">ZIP</span><span className="selected-file-copy"><strong>{file.name}</strong><small>{(file.size/1024/1024).toFixed(2)} MB · Ready to analyze</small></span><button type="button" className="clear-file-button" onClick={e=>{e.preventDefault();setFile(null);setFileError('');const input=document.getElementById('zip-file') as HTMLInputElement|null;if(input)input.value='';}} aria-label="Remove selected ZIP">×</button></div>}{file&&<div className="zip-submit"><label className="field-label" htmlFor="zip-label">Project label</label><input id="zip-label" className="text-input" value={label} onChange={e=>setLabel(e.target.value)} placeholder="Optional display name"/><button className="btn btn-primary full-button upload-submit-button" onClick={()=>onSubmitFile(file,label,audience,{include_security:security,include_quality:quality,include_architecture:architecture})} disabled={busy}>{busy?'Preparing upload…':'Analyze ZIP'} <span>↗</span><i className="upload-button-progress"/></button></div>}</div>}
      <div className="option-section"><div className="option-heading"><span className="section-index">ANALYSIS SETTINGS</span><span className="step-counter">STEP 02 / 03</span></div><div className="check-option"><label><input type="checkbox" checked={security} onChange={e=>setSecurity(e.target.checked)}/><span className="fake-check">✓</span><span><strong>Security patterns</strong><small>Secrets, dangerous calls, and unsafe sinks</small></span></label><span className="option-code">S-01</span></div><div className="check-option"><label><input type="checkbox" checked={quality} onChange={e=>setQuality(e.target.checked)}/><span className="fake-check">✓</span><span><strong>Quality & maintainability</strong><small>Large files, TODO markers, tests, docs</small></span></label><span className="option-code">Q-02</span></div><div className="check-option"><label><input type="checkbox" checked={architecture} onChange={e=>setArchitecture(e.target.checked)}/><span className="fake-check">✓</span><span><strong>Architecture map</strong><small>Static imports and module relationships</small></span></label><span className="option-code">A-03</span></div><div className="form-two-col audience-setting"><div><label className="field-label" htmlFor="audience">Report audience</label><select id="audience" className="text-input" value={audience} onChange={e=>setAudience(e.target.value as 'mentor'|'developer')}><option value="developer">Developer / technical</option><option value="mentor">Student & mentor</option></select></div><div><label className="field-label">AI explanation</label><div className="ai-choice-note"><span className="status-dot"/> Optional; currently evidence-only by default</div></div></div><div className="step-final"><span className="step-counter">STEP 03 / 03</span><p>Review the source, then launch the analysis. Completion generates a four-page PDF with repository shape, severity charts, prioritized fixes, and coverage notes.</p></div></div>
    </section><aside className="intake-aside"><article className="panel aside-card"><span className="aside-number">01</span><h3>Repository inventory</h3><p>Language mix, files, source lines, dependencies, tests, and project essentials.</p><span className="aside-line"/></article><article className="panel aside-card"><span className="aside-number">02</span><h3>Evidence correlation</h3><p>Each finding includes a rule ID, location, confidence, evidence, and remediation.</p><span className="aside-line"/></article><article className="panel aside-card aside-card-orange"><span className="aside-number">03</span><h3>Mentor-ready PDF</h3><p>Repository map, severity charts, prioritized fixes, and an engineering-intelligence brief.</p><span className="aside-line"/></article><div className="security-note"><span>◇</span><div><strong>Secure by default</strong><p>Source content is treated as untrusted input. Unsupported/binary files are skipped; credential-like evidence is redacted.</p></div></div></aside></div>
  </div>;
}

function HistoryPage({ items, busy, onRefresh, onOpen }: {items:Record<string,unknown>[];busy:boolean;onRefresh:()=>void;onOpen:(id:string)=>void}) {
  return <div className="page-stack"><section className="page-title-row"><div><span className="eyebrow"><span className="eyebrow-dot"/> HISTORY / 04</span><h1>Every scan, one baseline.</h1><p className="subtitle">Revisit completed snapshots, review results, and download reports.</p></div><button className="btn btn-outline" onClick={onRefresh} disabled={busy}>↻ Refresh</button></section><section className="panel history-panel"><div className="panel-head"><div><span className="section-index">ANALYSIS ARCHIVE</span><h2>Recent analyses</h2></div><span className="panel-tag">{items.length} RECORDS</span></div>{!items.length?<div className="empty-panel"><span className="empty-mark">◷</span><h3>No saved analysis yet</h3><p>Submitted scans and completed reports will appear here.</p></div>:<div className="history-list">{items.map((item,i)=><button className="history-row" key={String(item.id||i)} onClick={()=>item.id&&onOpen(String(item.id))}><span className="history-icon">{item.status==='completed'?'✓':item.status==='failed'?'!':'◷'}</span><span className="history-main"><strong>{String(item.project||'Codebase analysis')}</strong><small>{String(item.source&&typeof item.source==='object'?(item.source as Record<string,unknown>).repository_url||'Uploaded source':'Source not specified')}</small></span><span className={`job-status status-${String(item.status||'queued')}`}>{String(item.status||'queued')}</span><span className="history-time">{formatTimestamp(item.created_at)}</span><span className="row-arrow">↗</span></button>)}</div>}</section></div>;
}

function AskSentinalPanel({ job, provider, onNavigate }: { job: AnalysisJob | null; provider: string; onNavigate: (page: Page) => void }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState('');
  const [sending, setSending] = useState(false);
  const [chatError, setChatError] = useState('');
  const [selectedPath, setSelectedPath] = useState('');
  const ready = Boolean(job?.id && job.status === 'completed' && job.analysis);
  const canAsk = ready && provider === 'ollama';
  const prompts = ['What should I fix first?', 'Explain the high-risk findings.', 'Why is the health score not 100?'];

  useEffect(() => { setMessages([]); setQuestion(''); setChatError(''); setSelectedPath(''); }, [job?.id]);

  const send = async (value = question) => {
    const text = value.trim();
    if (!text || sending || !job?.id || !canAsk) return;
    const prior = messages.slice(-6);
    setMessages(previous => [...previous, { role: 'user', content: text }]);
    setQuestion(''); setSending(true); setChatError('');
    try {
      const response = await api.askSentinal(job.id, text, prior, selectedPath || undefined);
      setMessages(previous => [...previous, { role: 'assistant', content: response.answer }]);
    } catch (err) {
      setChatError(err instanceof Error ? err.message : 'Ask Sentinal could not answer this question.');
    } finally { setSending(false); }
  };

  return <div className="page-stack ask-page">
    <section className="page-title-row"><div><span className="eyebrow"><span className="eyebrow-dot"/> LOCAL MODEL / 06</span><h1>Ask <em>Sentinal.</em></h1><p className="subtitle">Small, practical questions answered from the evidence in your selected analysis.</p></div><span className="model-badge"><i/> {provider === 'ollama' ? 'OLLAMA CONNECTED BY CONFIG' : 'LOCAL MODEL NOT ENABLED'}</span></section>
    {!ready ? <section className="panel ask-gate"><div className="ask-gate-icon">✳</div><h2>Select a completed code review first</h2><p>Ask Sentinal uses the saved metrics and findings from one completed snapshot. It does not independently inspect arbitrary files or execute code.</p><button className="btn btn-primary btn-pill" onClick={() => onNavigate('History')}>Choose from history ↗</button></section> : provider !== 'ollama' ? <section className="panel ask-gate"><div className="ask-gate-icon">⌁</div><h2>Ollama is not the configured provider</h2><p>Set <code>AI_PROVIDER=ollama</code> in your local backend environment and restart the backend. Ask Sentinal deliberately does not switch to Bedrock or another paid provider automatically.</p><button className="btn btn-outline btn-pill" onClick={() => onNavigate('Settings')}>View settings ↗</button></section> : <div className="ask-layout">
      <section className="panel chat-panel"><div className="chat-topline"><div className="chat-avatar">S<span>✳</span></div><div><strong>Sentinal assistant</strong><span>Grounded in {job?.project} · {job?.analysis?.findings.length || 0} findings in snapshot</span></div><span className="chat-live-pill"><i/> LOCAL</span></div>
        <div className="chat-context-strip"><span>ANALYSIS CONTEXT</span><strong>{job?.project}</strong><span>{job?.analysis?.summary.files_analyzed.toLocaleString()} files · {job?.analysis?.summary.findings_total.toLocaleString()} signals</span></div>
        <div className="chat-thread" aria-live="polite">{!messages.length && <div className="chat-welcome"><span className="chat-spark">✳</span><h2>What would you like to understand?</h2><p>Ask one focused question. Answers are limited to the evidence available in this snapshot.</p><div className="suggested-prompts">{prompts.map(prompt => <button key={prompt} className="prompt-chip" onClick={() => void send(prompt)} disabled={sending}>{prompt} <span>↗</span></button>)}</div></div>}{messages.map((message, index) => <article className={`chat-message ${message.role === 'user' ? 'chat-message-user' : 'chat-message-assistant'}`} key={`${message.role}-${index}`}><span className="message-role">{message.role === 'user' ? 'YOU' : 'SENTINAL'}</span><p>{message.content}</p></article>)}{sending && <article className="chat-message chat-message-assistant"><span className="message-role">SENTINAL</span><p className="thinking-text"><span/> Reading the saved evidence…</p></article>}</div>
        {chatError && <div className="notice notice-error chat-error">{chatError}</div>}
        <form className="chat-composer" onSubmit={event => { event.preventDefault(); void send(); }}><textarea value={question} onChange={event => setQuestion(event.target.value)} maxLength={600} rows={2} placeholder="Ask about risk, a file, or what to fix first…" disabled={!canAsk || sending} aria-label="Ask Sentinal a question"/><div className="composer-bottom"><span>{question.length}/600 · Answers are evidence-bound</span><button className="btn btn-primary btn-pill" type="submit" disabled={!question.trim() || sending}>{sending ? 'Thinking…' : 'Ask question'} <span>↗</span></button></div></form>
      </section>
      <aside className="ask-sidebar"><section className="panel ask-side-card"><span className="section-index">OPTIONAL FILE CONTEXT</span><h3>Focus on one file</h3><p>Choose a file to prioritize findings for your next question.</p><select value={selectedPath} onChange={event => setSelectedPath(event.target.value)} aria-label="Select file context"><option value="">Whole codebase</option>{(job?.analysis?.files || []).map(file => <option key={file.path} value={file.path}>{file.path}</option>)}</select>{selectedPath && <div className="selected-file-hint">Selected context: <strong>{selectedPath}</strong></div>}</section><section className="panel ask-side-card ask-limits"><span className="section-index">HONEST BY DESIGN</span><h3>What it can—and can't—do</h3><ul><li>Explain recorded findings and scanner metrics.</li><li>Suggest a practical order for human review.</li><li>Admit when the snapshot lacks enough evidence.</li><li>Does not run code or query live CVE advisories.</li></ul></section></aside>
    </div>}
  </div>;
}

function ProfilePage({ user, themePreference, onThemeChange, onSignOut }: { user: SessionUser; themePreference: ThemePreference; onThemeChange: (value: ThemePreference) => void; onSignOut: () => void }) {
  const [profile, setProfile] = useState<ProfileData>(() => emptyProfile(user.username));
  const [baseline, setBaseline] = useState<ProfileData>(() => emptyProfile(user.username));
  const [editing, setEditing] = useState(true);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [github, setGithub] = useState<GitHubOverview | null>(null);
  const [githubBusy, setGithubBusy] = useState(false);
  const [avatarFailed, setAvatarFailed] = useState(false);
  const photoInput = useRef<HTMLInputElement>(null);
  useEffect(() => { let mounted = true; setLoading(true); void api.getProfile().then((loaded) => { if (!mounted) return; const merged = { ...emptyProfile(user.username), ...loaded, email: loaded.email || (user.username.includes('@') ? user.username : '') } as ProfileData; setProfile(merged); setBaseline(merged); setEditing(!merged.created_at || (!merged.full_name && !merged.headline && !merged.bio && !merged.github_username)); }).catch((e) => { if (mounted) { setError(e instanceof Error ? e.message : 'Could not load profile.'); setEditing(true); } }).finally(() => { if (mounted) setLoading(false); }); return () => { mounted = false; }; }, [user.username]);
  const patch = (key: keyof ProfileData, value: string | boolean | string[]) => { if (key === 'avatar_data_url') setAvatarFailed(false); setProfile(current => ({ ...current, [key]: value })); };
  const updateList = (key: 'preferred_languages' | 'technical_skills' | 'interests', value: string) => patch(key, value.split(',').map(x => x.trim()).filter(Boolean).slice(0, key === 'technical_skills' ? 60 : 30));
  const uploadPhoto = (file?: File) => { if (!file) return; setError(''); if (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type)) { setError('Choose a PNG, JPEG, or WebP image.'); return; } if (file.size > 256 * 1024) { setError('Profile images must be 256 KB or smaller.'); return; } const reader = new FileReader(); reader.onload = () => { if (typeof reader.result === 'string') patch('avatar_data_url', reader.result); }; reader.onerror = () => setError('Could not read this image. Try a different file.'); reader.readAsDataURL(file); };
  const save = async (event: FormEvent) => { event.preventDefault(); setError(''); setMessage(''); if (profile.website && !/^https?:\/\//i.test(profile.website)) { setError('Website must begin with https:// or http://.'); return; } const githubUrl = profile.github_url || (profile.github_username ? `https://github.com/${profile.github_username.replace(/^@/, '')}` : ''); if (githubUrl && !/^https?:\/\//i.test(githubUrl)) { setError('GitHub URL must begin with https:// or http://.'); return; } setSaving(true); try { const saved = await api.saveProfile({ ...profile, github_url: githubUrl }); setProfile(saved); setBaseline(saved); setEditing(false); setMessage('Profile saved to your Sentinal workspace.'); } catch (e) { setError(e instanceof Error ? e.message : 'Could not save profile.'); } finally { setSaving(false); } };
  const loadGithub = async () => { const username = profile.github_username.trim().replace(/^@/, ''); if (!username) { setError('Enter a GitHub username first.'); return; } setGithubBusy(true); setError(''); try { const data = await api.githubOverview(username); setGithub(data); if (data.avatar_url && !profile.avatar_data_url) { /* Remote avatar stays remote; it is not copied into private profile storage. */ } } catch (e) { setError(e instanceof Error ? e.message : 'Could not load this public GitHub profile.'); } finally { setGithubBusy(false); } };
  const cancel = () => { setProfile(baseline); setError(''); setMessage(''); setEditing(false); };
  const avatar = profile.avatar_data_url || (profile.github_username ? `https://github.com/${encodeURIComponent(profile.github_username.replace(/^@/, ''))}.png?size=160` : '');
  const joined = profile.created_at ? new Date(profile.created_at).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' }) : 'Not available yet';
  return <div className="page-stack profile-page">
    <section className="page-title-row"><div><span className="eyebrow"><span className="eyebrow-dot"/> DEVELOPER IDENTITY</span><h1>Your profile, <em>your workspace.</em></h1><p className="subtitle">Manage your developer identity and the preferences Sentinal uses for this workspace.</p></div>{!editing && <button type="button" className="btn btn-primary btn-pill" onClick={() => { setEditing(true); setMessage(''); }}><AppIcon name="user" size={17}/> Edit profile</button>}</section>
    {error && <div className="notice notice-error" role="alert"><span>{error}</span><button type="button" onClick={() => setError('')} aria-label="Dismiss error">×</button></div>}{message && <div className="notice notice-success" role="status">{message}</div>}
    {loading ? <section className="panel profile-loading"><span className="auth-loading-indicator"><i/>Loading saved profile…</span></section> : <form onSubmit={save} className="profile-layout">
      <section className="panel profile-identity-card"><div className="profile-avatar-wrap">{avatar && !avatarFailed ? <img className="profile-avatar-image" src={avatar} alt="Profile avatar preview" onError={() => setAvatarFailed(true)}/> : <span className="profile-avatar-fallback"><AppIcon name="user-round" size={42}/></span>}{editing && <button type="button" className="avatar-edit-button" onClick={() => photoInput.current?.click()} aria-label="Upload profile image"><AppIcon name="image" size={17}/></button>}</div><input ref={photoInput} hidden type="file" accept="image/png,image/jpeg,image/webp" onChange={event => uploadPhoto(event.target.files?.[0])}/>{editing && <div className="avatar-actions"><button type="button" className="btn btn-outline btn-pill" onClick={() => photoInput.current?.click()}>{profile.avatar_data_url ? 'Change image' : 'Upload image'}</button>{profile.avatar_data_url && <button type="button" className="text-action" onClick={() => patch('avatar_data_url', '')}>Remove uploaded image</button>}</div>}<h2>{profile.full_name || profile.username || user.username || 'Developer'}</h2><p className="profile-handle">@{profile.username || (user.username.includes('@') ? user.username.split('@')[0] : user.username)}</p><p className="profile-headline">{profile.headline || 'Add a headline to introduce your work.'}</p><div className="profile-account-status"><i/>{user.localMode ? 'Local workspace' : 'Authenticated account'}</div><div className="profile-meta-list"><span><AppIcon name="mail" size={15}/>{profile.email || user.username || 'Email not available'}</span><span><AppIcon name="calendar" size={15}/>{profile.created_at ? `Profile created ${joined}` : 'Profile created date not available'}</span></div><div className="profile-identity-divider"/><div className="profile-preferences-mini"><label className="field-label">Default dashboard</label>{editing ? <select className="text-input" value={profile.default_dashboard} onChange={e => patch('default_dashboard', e.target.value)}><option>Home</option><option>Findings</option><option>Architecture</option><option>History</option></select> : <strong>{profile.default_dashboard || 'Home'}</strong>}</div><button type="button" className="btn btn-outline profile-signout" onClick={onSignOut}><AppIcon name="log-out" size={16}/> Sign out</button></section>
      <div className="profile-content">
        <section className="panel profile-section"><div className="profile-section-heading"><span className="profile-section-icon"><AppIcon name="user-round" size={18}/></span><div><h2>Profile identity</h2><p>Tell teammates who you are and what you focus on.</p></div></div><div className="profile-form-grid"><div className="profile-field"><label className="field-label" htmlFor="profile-full-name">Full name</label><input id="profile-full-name" className="text-input" value={profile.full_name} onChange={e => patch('full_name', e.target.value)} disabled={!editing} placeholder="Your name"/></div><div className="profile-field"><label className="field-label" htmlFor="profile-username">Username</label><input id="profile-username" className="text-input" value={profile.username} onChange={e => patch('username', e.target.value)} disabled={!editing} placeholder="developer_handle" pattern="[A-Za-z0-9._-]{1,80}" title="Use letters, numbers, dots, underscores, or hyphens"/></div><div className="profile-field profile-field-span"><label className="field-label" htmlFor="profile-headline">Professional headline</label><input id="profile-headline" className="text-input" value={profile.headline} onChange={e => patch('headline', e.target.value)} disabled={!editing} placeholder="e.g. Full-stack developer · Cloud engineering"/></div><div className="profile-field profile-field-span"><label className="field-label" htmlFor="profile-bio">Short biography</label><textarea id="profile-bio" className="text-input profile-textarea" value={profile.bio} onChange={e => patch('bio', e.target.value)} disabled={!editing} maxLength={1200} placeholder="A few lines about your experience, interests, or current work."/><small>{profile.bio.length}/1200 characters</small></div><div className="profile-field"><label className="field-label" htmlFor="profile-role">Role / experience</label><input id="profile-role" className="text-input" value={profile.role} onChange={e => patch('role', e.target.value)} disabled={!editing} placeholder="e.g. Student developer"/></div><div className="profile-field"><label className="field-label" htmlFor="profile-location">Location (optional)</label><input id="profile-location" className="text-input" value={profile.location} onChange={e => patch('location', e.target.value)} disabled={!editing} placeholder="City or region"/></div><div className="profile-field"><label className="field-label" htmlFor="profile-website">Website / portfolio</label><input id="profile-website" className="text-input" type="url" value={profile.website} onChange={e => patch('website', e.target.value)} disabled={!editing} placeholder="https://example.com"/></div><div className="profile-field"><label className="field-label" htmlFor="profile-email">Email</label><input id="profile-email" className="text-input" type="email" value={profile.email} onChange={e => patch('email', e.target.value)} disabled={!editing} placeholder="you@example.com"/></div></div></section>
        <section className="panel profile-section"><div className="profile-section-heading"><span className="profile-section-icon"><AppIcon name="code" size={18}/></span><div><h2>Developer identity</h2><p>Link your public GitHub profile and add skills manually. Repository information is fetched from GitHub when available.</p></div></div><div className="profile-form-grid"><div className="profile-field"><label className="field-label" htmlFor="profile-github-user">GitHub username</label><input id="profile-github-user" className="text-input" value={profile.github_username} onChange={e => patch('github_username', e.target.value.replace(/^@/, ''))} disabled={!editing} placeholder="octocat"/></div><div className="profile-field"><label className="field-label" htmlFor="profile-github-url">GitHub profile URL</label><input id="profile-github-url" className="text-input" type="url" value={profile.github_url} onChange={e => patch('github_url', e.target.value)} disabled={!editing} placeholder="https://github.com/username"/></div><div className="profile-field profile-field-span"><label className="field-label" htmlFor="profile-languages">Preferred programming languages <span className="field-secondary">Comma separated</span></label><input id="profile-languages" className="text-input" value={profile.preferred_languages.join(', ')} onChange={e => updateList('preferred_languages', e.target.value)} disabled={!editing} placeholder="TypeScript, Python, Go"/></div><div className="profile-field profile-field-span"><label className="field-label" htmlFor="profile-skills">Technical skills <span className="field-secondary">Comma separated</span></label><input id="profile-skills" className="text-input" value={profile.technical_skills.join(', ')} onChange={e => updateList('technical_skills', e.target.value)} disabled={!editing} placeholder="AWS, FastAPI, React, SQL"/></div><div className="profile-field profile-field-span"><label className="field-label" htmlFor="profile-interests">Areas of interest <span className="field-secondary">Comma separated</span></label><input id="profile-interests" className="text-input" value={profile.interests.join(', ')} onChange={e => updateList('interests', e.target.value)} disabled={!editing} placeholder="Application security, developer tools, AI"/></div></div><div className="profile-github-actions">{profile.github_username && <a className="btn btn-outline btn-pill" href={profile.github_url || `https://github.com/${profile.github_username}`} target="_blank" rel="noreferrer"><AppIcon name="external-link" size={15}/> Open GitHub profile</a>}<button className="btn btn-primary btn-pill" type="button" onClick={() => void loadGithub()} disabled={githubBusy || !profile.github_username}>{githubBusy ? 'Loading GitHub…' : 'Load public GitHub overview'} <AppIcon name="arrow-up-right" size={15}/></button></div>{github && <div className="github-overview"><div className="github-overview-head"><img src={github.avatar_url} alt={`${github.login} GitHub avatar`}/><div><strong>{github.name || github.login}</strong><span>@{github.login} · Public GitHub data</span>{github.bio && <p>{github.bio}</p>}</div><a href={github.html_url} target="_blank" rel="noreferrer" aria-label="Open GitHub profile"><AppIcon name="external-link" size={16}/></a></div><div className="github-stats"><div><strong>{github.public_repos}</strong><small>Public repositories</small></div><div><strong>{github.followers}</strong><small>Followers</small></div><div><strong>{github.following}</strong><small>Following</small></div></div><div className="github-repo-list">{github.repositories.map(repo => <a key={repo.name} href={repo.html_url} target="_blank" rel="noreferrer"><span><strong>{repo.name}</strong><small>{repo.description || 'No description provided'}</small></span><em>{repo.language || 'Not specified'} · ★ {repo.stargazers_count}</em></a>)}</div></div>}</section>
        <section className="panel profile-section"><div className="profile-section-heading"><span className="profile-section-icon"><AppIcon name="palette" size={18}/></span><div><h2>Workspace preferences</h2><p>Choose the visual environment and profile-level defaults.</p></div></div><div className="profile-preference-row"><div><strong>Appearance</strong><small>A consistent light interface across your workspace.</small></div><ThemePreferenceControl/></div><div className="profile-preference-row"><div><strong>Analysis notifications</strong><small>Saved preference for analysis notifications; critical errors remain visible in the workspace.</small></div><label className="profile-switch"><input type="checkbox" checked={profile.notifications_enabled} onChange={e => patch('notifications_enabled', e.target.checked)} disabled={!editing}/><span/></label></div><div className="profile-preference-row"><div><strong>Public profile visibility</strong><small>Saved as a preference; a public profile publishing endpoint is not enabled.</small></div><label className="profile-switch"><input type="checkbox" checked={profile.privacy_profile_public} onChange={e => patch('privacy_profile_public', e.target.checked)} disabled={!editing}/><span/></label></div><div className="profile-preference-row"><div><strong>Public email visibility</strong><small>Keep this disabled unless you intend to show it.</small></div><label className="profile-switch"><input type="checkbox" checked={profile.email_public} onChange={e => patch('email_public', e.target.checked)} disabled={!editing}/><span/></label></div></section>
        {editing && <div className="profile-form-actions"><button type="button" className="btn btn-outline btn-pill" onClick={cancel} disabled={saving}>Cancel</button><button type="submit" className="btn btn-primary btn-pill" disabled={saving}>{saving ? 'Saving profile…' : 'Save changes'} <AppIcon name="save" size={16}/></button></div>}
      </div>
    </form>}
  </div>;
}

function App() {
  const [user,setUser]=useState<SessionUser|null>(()=>import.meta.env.DEV&&!cloudAuthEnabled&&sessionStorage.getItem('sentinal-local-workspace')==='1'?{username:'Local workspace',localMode:true}:null);
  const [authChecking, setAuthChecking] = useState(cloudAuthEnabled);
  const [page,setPage]=useState<Page>('Home'); const [job,setJob]=useState<AnalysisJob|null>(null); const [busy,setBusy]=useState(false); const [error,setError]=useState(''); const [health,setHealth]=useState<{execution_mode:string;ai_provider:string}|null>(null); const [history,setHistory]=useState<Record<string,unknown>[]>([]);
  const [themePreference] = useState<ThemePreference>('light');
  const setThemePreference = (_value: ThemePreference) => undefined;
  useEffect(() => { document.documentElement.dataset.theme = 'light'; document.documentElement.dataset.themePreference = 'light'; document.documentElement.style.colorScheme = 'light'; document.querySelector('meta[name="theme-color"]')?.setAttribute('content', '#F8F6F0'); localStorage.setItem('sentinal-theme', 'light'); }, []);
  useEffect(() => {
    if (!cloudAuthEnabled) { setAuthChecking(false); return; }
    let active = true;
    void restoreSession().then((restored) => { if (active) setUser(restored); }).finally(() => { if (active) setAuthChecking(false); });
    return () => { active = false; };
  }, []);
  const poll = useCallback(async(id:string)=>{
    try { const result=await api.getAnalysis(id); setJob(result); if(['completed','failed'].includes(result.status)){setBusy(false);void api.history().then(v=>setHistory(v.items)).catch(()=>{});} }
    catch(e){setError(e instanceof Error?e.message:'Could not refresh analysis status.');setBusy(false);}
  },[]);
  useEffect(()=>{if(user){void api.health().then(setHealth).catch(()=>setHealth({execution_mode:'local',ai_provider:'disabled'}));void api.history().then(v=>setHistory(v.items)).catch(()=>{});}},[user]);
  useEffect(() => { if (!user) return; let active = true; void api.getProfile().then(profile => { if (active && ['Home', 'Findings', 'Architecture', 'History'].includes(profile.default_dashboard)) setPage(profile.default_dashboard as Page); }).catch(() => undefined); return () => { active = false; }; }, [user?.username]);
  useEffect(()=>{if(!job?.id||!['queued','analyzing','explaining','reporting'].includes(job.status))return;setBusy(true);const timer=window.setInterval(()=>void poll(job.id),1800);void poll(job.id);return()=>window.clearInterval(timer);},[job?.id,job?.status,poll]);
  const startJob=async(promise:Promise<AnalysisJob>)=>{setBusy(true);setError('');setPage('Home');try{const submitted=await promise;setJob(submitted);void poll(submitted.id);}catch(e){setError(e instanceof Error?e.message:'Could not submit the analysis.');setBusy(false);}};
  const submitRepo=(data:Parameters<typeof api.submitRepo>[0])=>void startJob(api.submitRepo(data));
  const submitFile=(file:File,label:string,audience:'mentor'|'developer',options:{include_security:boolean;include_quality:boolean;include_architecture:boolean})=>void startJob(api.uploadZip(file,label,audience,options));
  const updateFinding=async(f:Finding,status:string)=>{if(!job?.id||!job.analysis)return;try{await api.updateFinding(job.id,f.id,status,f.note||'');setJob({...job,analysis:{...job.analysis,findings:job.analysis.findings.map(x=>x.id===f.id?{...x,status}:x)}});}catch(e){setError(e instanceof Error?e.message:'Could not update the finding.');}};
  const downloadReport = async (): Promise<boolean> => {
    if (!job?.id) return false;
    if (job.status !== 'completed') {
      setError('Your analysis is still running. Please wait until the report is ready.');
      return false;
    }
    setError('');
    try {
      const token = await sessionToken();
      const response = await fetch(api.reportUrl(job.id), { headers: token ? { Authorization: `Bearer ${token}` } : {} });
      if (response.status === 409) {
        setError('The PDF is still being generated. Please wait a moment and try again.');
        return false;
      }
      if (!response.ok) throw new Error(`PDF download failed (HTTP ${response.status}).`);
      const blob = await response.blob();
      const href = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = href;
      a.download = `sentinal-${job.id}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.setTimeout(() => URL.revokeObjectURL(href), 1000);
      return true;
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not download the PDF report.');
      return false;
    }
  };
  const login=(next:SessionUser)=>{setUser(next);if(import.meta.env.DEV&&next.localMode)sessionStorage.setItem('sentinal-local-workspace','1');};
  const logout=()=>{signOut();sessionStorage.removeItem('sentinal-local-workspace');setUser(null);setJob(null);setPage('Home');};
  const openHistory=async(id:string)=>{try{const record=await api.getAnalysis(id);setJob(record);setPage('Home');}catch(e){setError(e instanceof Error?e.message:'Could not open analysis.');}};
  if (authChecking) return <div className="auth-loading-shell"><Brand/><span className="auth-loading-indicator"><i/>Checking your secure session…</span></div>;
  if(!user)return <LoginScreen onLogin={login} themePreference={themePreference} onThemeChange={setThemePreference}/>;
  const analysis=job?.analysis||null;
  return <div className="app-shell">
    <main className="main-area">
      <div className="content-area">{error&&<div className="notice notice-error global-error" role="alert"><span>{error}</span><button onClick={()=>setError('')} aria-label="Dismiss error">×</button></div>}
        {page==='Home'&&<Home job={job} busy={busy} onNew={()=>setPage('New analysis')} onDownload={downloadReport} onNavigate={setPage} history={history} onOpenHistory={openHistory}/>}
        {page==='New analysis'&&<NewAnalysis onSubmitRepo={submitRepo} onSubmitFile={submitFile} busy={busy}/>}
        {page==='Findings'&&<div className="page-stack"><section className="page-title-row"><div><span className="eyebrow"><span className="eyebrow-dot"/> EVIDENCE REGISTER / 02</span><h1>Findings with context.</h1><p className="subtitle">Every signal is tied to a rule, location, confidence, and suggested remediation.</p></div>{analysis&&<DownloadActionButton onDownload={downloadReport} disabled={job?.status!=='completed'} label="Download report"/>}</section>{analysis&&job?<FindingsTable analysis={analysis} onUpdate={updateFinding}/>:<div className="panel"><div className="empty-panel"><span className="empty-mark">≡</span><h3>No findings to review yet</h3><p>Run an analysis to view evidence-linked security and quality signals.</p><button className="btn btn-primary" onClick={()=>setPage('New analysis')}>Start an analysis ↗</button></div></div>}</div>}
        {page==='Architecture'&&<div className="page-stack"><section className="page-title-row"><div><span className="eyebrow"><span className="eyebrow-dot"/> REPO ATLAS / 03</span><h1>See how the pieces connect.</h1><p className="subtitle">A static view of inferred module relationships from imports and requires.</p></div><span className="panel-tag">{analysis?.architecture.nodes.length??0} NODES · {analysis?.architecture.edges.length??0} EDGES</span></section><section className="panel architecture-panel"><div className="panel-head"><div><span className="section-index">DEPENDENCY MAP</span><h2>{analysis?.project||'No project selected'}</h2></div><span className="panel-tag">STATIC INFERENCE</span></div><ArchitectureMap analysis={analysis}/><p className="panel-footnote">{analysis?.architecture.scope_note||'Dynamic loading, runtime-only relationships, and external package internals may not be represented.'}</p></section><section className="panel"><div className="panel-head"><div><span className="section-index">MODULE INVENTORY</span><h2>Largest source units</h2></div></div>{analysis?<div className="module-list">{analysis.files.slice(0,18).map(f=>{const fileFindings=analysis.findings.filter(x=>x.path===f.path);const critical=fileFindings.some(x=>x.severity==='CRITICAL'||x.severity==='HIGH');return <div className="module-row" key={f.path}><span className="module-file-icon">{f.language==='Python'?'Py':f.language==='JavaScript'?'JS':f.language==='TypeScript'?'TS':f.language.slice(0,2)}</span><span className="module-path" title={f.path}>{f.path}</span><span className={`file-signal ${critical?'file-signal-risk':fileFindings.length?'file-signal-review':'file-signal-clear'}`}>{fileFindings.length?`${fileFindings.length} signal${fileFindings.length===1?'':'s'}`:'No signal'}</span><strong>{f.loc.toLocaleString()} LOC</strong></div>})}</div>:<p className="panel-empty-copy">Run a scan to populate the module inventory.</p>}</section></div>}
        {page==='Ask Sentinal'&&<AskSentinalPanel job={job} provider={health?.ai_provider || 'disabled'} onNavigate={setPage}/> }
        {page==='History'&&<HistoryPage items={history} busy={busy} onRefresh={()=>void api.history().then(v=>setHistory(v.items)).catch(e=>setError(String(e)))} onOpen={openHistory}/>}
        {page==='Profile'&&<ProfilePage user={user} themePreference={themePreference} onThemeChange={setThemePreference} onSignOut={logout}/>}
        {page==='Settings'&&<div className="page-stack"><section className="page-title-row"><div><span className="eyebrow"><span className="eyebrow-dot"/> PREFERENCES / 05</span><h1>Keep the boundaries clear.</h1><p className="subtitle">Control analysis behavior, AI options, and how to run this workspace.</p></div></section><section className="panel appearance-panel"><div className="appearance-copy"><span className="settings-icon"><AppIcon name="palette" size={20}/></span><div><span className="section-index">VISUAL STYLE</span><h2>Appearance</h2><p>Sentinal uses a clear, consistent light interface.</p></div></div><ThemePreferenceControl/></section><section className="settings-grid"><article className="panel settings-card"><span className="settings-icon">⌘</span><span className="section-index">RUNTIME</span><h2>Execution environment</h2><p>Sentinal reads supported files and runs deterministic parsers. Submitted code is never executed as part of a normal scan.</p><div className="settings-detail"><span>Mode</span><strong>{health?.execution_mode||'checking…'}</strong></div><div className="settings-detail"><span>API</span><strong>{'http://localhost:8000'}</strong></div></article><article className="panel settings-card"><span className="settings-icon settings-icon-orange">✳</span><span className="section-index">AI EXPLANATION</span><h2>Optional narrative layer</h2><p>AI explanation is constrained to redacted structured findings. Counts, locations, and chart values stay grounded in deterministic analysis.</p><div className="settings-detail"><span>Configured provider</span><strong>{health?.ai_provider||'disabled'}</strong></div><div className="settings-inline-note">Bedrock or OpenAI inference may incur usage charges. Review privacy and cost before enabling.</div></article><article className="panel settings-card"><span className="settings-icon">▤</span><span className="section-index">REPORTS</span><h2>Export and evidence</h2><p>Completed scans export a four-page report with severity charts, prioritized remediation, and coverage notes. It distinguishes observed evidence from inferred guidance.</p><div className="settings-detail"><span>Last report</span><strong>{job?.status==='completed'?'Ready to download':'Not generated yet'}</strong></div><DownloadActionButton onDownload={downloadReport} disabled={job?.status!=='completed'} label="Download latest report"/></article><article className="panel settings-card"><span className="settings-icon settings-icon-orange">◇</span><span className="section-index">DATA & PRIVACY</span><h2>Know what is retained</h2><p>Local mode persists analysis metadata and results in SQLite. Uploaded archive copies are filtered and deleted after processing. AWS retention depends on your deployed bucket lifecycle settings.</p><div className="settings-detail"><span>Local storage</span><strong>backend/data/</strong></div><div className="settings-inline-note">Never upload production secrets. Credential-like evidence is redacted, but the scanner cannot guarantee that all sensitive data is recognized.</div></article></section></div>}
      </div>
    </main>
    <FloatingDock page={page} onNavigate={setPage} canDownload={job?.status==='completed'} onDownload={downloadReport}/>
  </div>;
}

export default App;
