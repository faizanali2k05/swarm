import React from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Blockchain from './pages/Blockchain'
import './styles.css'

function App(){
  return (
    <BrowserRouter>
      <div style={{padding:20}}>
        <nav style={{marginBottom:10}}>
          <Link to="/">Dashboard</Link> | <Link to="/chain">Blockchain</Link>
        </nav>
        <Routes>
          <Route path="/" element={<Dashboard/>} />
          <Route path="/chain" element={<Blockchain/>} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}

createRoot(document.getElementById('root')).render(<App />)
