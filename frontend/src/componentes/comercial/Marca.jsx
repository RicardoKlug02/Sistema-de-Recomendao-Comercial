import logo from '../../assets/logo-rio-verde.png'

// O import gera um endereço em /assets, servido tanto pelo Vite quanto pelo FastAPI.
export default function Marca() {
  return (
    <img
      className="logo-rio-verde"
      src={logo}
      alt="Rio Verde Representações"
      width="717"
      height="269"
    />
  )
}
