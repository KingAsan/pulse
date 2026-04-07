import { Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import HomePage from './pages/HomePage'
import MoviesPage from './pages/MoviesPage'
import BooksPage from './pages/BooksPage'
import MusicPage from './pages/MusicPage'
import EventsPage from './pages/EventsPage'
import CinemaPage from './pages/CinemaPage'
import ProfilePage from './pages/ProfilePage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DetailPage from './pages/DetailPage'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/movies" element={<MoviesPage />} />
        <Route path="/movies/:id" element={<DetailPage type="movie" />} />
        <Route path="/books" element={<BooksPage />} />
        <Route path="/books/:id" element={<DetailPage type="book" />} />
        <Route path="/music" element={<MusicPage />} />
        <Route path="/events" element={<EventsPage />} />
        <Route path="/cinema" element={<CinemaPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Route>
    </Routes>
  )
}
