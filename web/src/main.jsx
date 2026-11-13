import React from 'react'
import { createRoot } from 'react-dom/client'
import '@fontsource/archivo/400.css'
import '@fontsource/archivo/500.css'
import '@fontsource/archivo/700.css'
import '@fontsource/sofia-sans-condensed/600.css'
import '@fontsource/sofia-sans-condensed/700.css'
import 'leaflet/dist/leaflet.css'
import './styles.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(<App />)
