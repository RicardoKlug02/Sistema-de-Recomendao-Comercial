import Icone from './Icone'

export default function EstadoVazio({
  titulo = 'Nenhum resultado por aqui',
  descricao = 'Experimente ajustar a busca ou os filtros para encontrar outros clientes.',
}) {
  return (
    <div className="estado-vazio" role="status">
      <Icone nome="busca" tamanho={28} />
      <h3>{titulo}</h3>
      <p>{descricao}</p>
    </div>
  )
}
