import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './estilos/index.css'
import Aplicacao from './Aplicacao.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Aplicacao />
  </StrictMode>,
)
