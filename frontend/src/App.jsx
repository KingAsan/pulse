import { Routes, Route } from 'react-router-dom'
import { Suspense, lazy } from 'react'
import Layout from './components/layout/Layout'

// Lazy load all pages for code splitting
const HomePage = lazy(() => import('./pages/HomePage'))
const MoviesPage = lazy(() => import('./pages/MoviesPage'))
const BooksPage = lazy(() => import('./pages/BooksPage'))
const MusicPage = lazy(() => import('./pages/MusicPage'))
const EventsPage = lazy(() => import('./pages/EventsPage'))
const CinemaPage = lazy(() => import('./pages/CinemaPage'))
const ProfilePage = lazy(() => import('./pages/ProfilePage'))
const LoginPage = lazy(() => import('./pages/LoginPage'))
const RegisterPage = lazy(() => import('./pages/RegisterPage'))
const DetailPage = lazy(() => import('./pages/DetailPage'))
const AIPage = lazy(() => import('./pages/AIPage'))

// Loading fallback component
const PageLoader = () => (
  <div className="loader" style={{ minHeight: '50vh' }}>
    <div className="spinner"></div>
  </div>
)

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Suspense fallback={<PageLoader />}><HomePage /></Suspense>} />
        <Route path="/movies" element={<Suspense fallback={<PageLoader />}><MoviesPage /></Suspense>} />
        <Route path="/movies/:id" element={<Suspense fallback={<PageLoader />}><DetailPage type="movie" /></Suspense>} />
        <Route path="/books" element={<Suspense fallback={<PageLoader />}><BooksPage /></Suspense>} />
        <Route path="/books/:id" element={<Suspense fallback={<PageLoader />}><DetailPage type="book" /></Suspense>} />
        <Route path="/music" element={<Suspense fallback={<PageLoader />}><MusicPage /></Suspense>} />
        <Route path="/events" element={<Suspense fallback={<PageLoader />}><EventsPage /></Suspense>} />
        <Route path="/cinema" element={<Suspense fallback={<PageLoader />}><CinemaPage /></Suspense>} />
        <Route path="/ai" element={<Suspense fallback={<PageLoader />}><AIPage /></Suspense>} />
        <Route path="/profile" element={<Suspense fallback={<PageLoader />}><ProfilePage /></Suspense>} />
        <Route path="/login" element={<Suspense fallback={<PageLoader />}><LoginPage /></Suspense>} />
        <Route path="/register" element={<Suspense fallback={<PageLoader />}><RegisterPage /></Suspense>} />
      </Route>
    </Routes>
  )
}
