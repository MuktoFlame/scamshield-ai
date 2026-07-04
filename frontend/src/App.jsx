import { useState } from 'react'
import { Link, NavLink, Route, Routes, useNavigate } from 'react-router-dom'
import { useAuth } from './lib/auth.jsx'
import HomePage from './pages/HomePage.jsx'
import ScanPage from './pages/ScanPage.jsx'
import WebsiteCheckPage from './pages/WebsiteCheckPage.jsx'
import NewsCheckPage from './pages/NewsCheckPage.jsx'
import ProductCheckPage from './pages/ProductCheckPage.jsx'
import HistoryPage from './pages/HistoryPage.jsx'
import LearnPage from './pages/LearnPage.jsx'
import LoginPage from './pages/LoginPage.jsx'
import RegisterPage from './pages/RegisterPage.jsx'
import FamilyPage from './pages/FamilyPage.jsx'
import AboutModelPage from './pages/AboutModelPage.jsx'

function NavItem({ to, children }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `rounded-lg px-4 py-2 font-semibold transition ${
          isActive
            ? 'bg-blue-100 text-blue-800'
            : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
        }`
      }
    >
      {children}
    </NavLink>
  )
}

export default function App() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [bigText, setBigText] = useState(false)

  const toggleBigText = () => {
    document.documentElement.classList.toggle('big-text', !bigText)
    setBigText(!bigText)
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center gap-3 px-4 py-3">
          <Link to="/" className="mr-2 flex items-center gap-2 text-xl font-extrabold tracking-tight text-blue-800">
            <span aria-hidden="true" className="text-2xl">🛡️</span> ScamShield AI
          </Link>
          <nav className="flex flex-wrap items-center gap-1" aria-label="Main">
            <NavItem to="/">Home</NavItem>
            <NavItem to="/check/message">Message</NavItem>
            <NavItem to="/check/website">Website</NavItem>
            <NavItem to="/check/news">News</NavItem>
            <NavItem to="/check/product">Product</NavItem>
            <NavItem to="/learn">Learn</NavItem>
            {user && <NavItem to="/history">History</NavItem>}
            {user && <NavItem to="/family">Family</NavItem>}
          </nav>
          <div className="ms-auto flex items-center gap-2">
            <button
              onClick={toggleBigText}
              className="btn-secondary !px-3 !py-1.5 text-sm"
              aria-pressed={bigText}
              title="Toggle larger text"
            >
              A<span className="text-lg leading-none">A</span>
            </button>
            {user ? (
              <>
                <span className="hidden text-sm text-slate-500 sm:inline">
                  {user.name} ({user.role})
                </span>
                <button
                  className="btn-secondary !py-1.5 text-sm"
                  onClick={() => {
                    logout()
                    navigate('/')
                  }}
                >
                  Sign out
                </button>
              </>
            ) : (
              <Link to="/login" className="btn-secondary !py-1.5 text-sm">
                Sign in
              </Link>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-8">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/check/message" element={<ScanPage />} />
          <Route path="/check/website" element={<WebsiteCheckPage />} />
          <Route path="/check/news" element={<NewsCheckPage />} />
          <Route path="/check/product" element={<ProductCheckPage />} />
          <Route path="/learn" element={<LearnPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/family" element={<FamilyPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/about-model" element={<AboutModelPage />} />
        </Routes>
      </main>

      <footer className="mx-auto max-w-5xl px-4 pb-8 text-sm text-slate-500">
        <p>
          ScamShield AI helps you spot warning signs. It is not a substitute for
          reporting fraud to your bank or the police.{' '}
          <Link to="/about-model" className="font-semibold text-blue-700 underline">
            How the AI works
          </Link>
        </p>
      </footer>
    </div>
  )
}
