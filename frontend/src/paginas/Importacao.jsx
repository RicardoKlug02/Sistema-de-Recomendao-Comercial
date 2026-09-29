<<<<<<< Updated upstream
import { useEffect, useRef, useState } from 'react'
import Cartao from '../componentes/Cartao'
import CartaoIndicador from '../componentes/CartaoIndicador'
import { importarArquivos, validarArquivo } from '../servicos/importacao'
import './Importacao.css'

// A API não expõe histórico: o resultado mostrado pertence apenas ao envio atual.
export default function Importacao({ usuario, ativa, aoImportar }) {
  const [arquivos, definirArquivos] = useState({ pedidos: null, itens: null })
  const [erro, definirErro] = useState('')
  const [enviando, definirEnviando] = useState(false)
  const [resultado, definirResultado] = useState(null)
  const envioEmCurso = useRef(false)
  const controle = useRef(null)
  const podeImportar = ['admin', 'gestor'].includes(usuario.perfil)
  useEffect(() => () => controle.current?.abort(), [])
  function selecionar(tipo, lista) {
    if (envioEmCurso.current || !lista.length) return
    const falha = lista.length !== 1 ? 'Selecione uma planilha para cada campo.' : validarArquivo(lista[0])
    definirErro(falha)
    // Uma seleção inválida não pode reutilizar um arquivo anterior sem aviso.
    definirArquivos((atuais) => ({ ...atuais, [tipo]: falha ? null : lista[0] }))
    definirResultado(null)
  }
  async function importar() {
    if (envioEmCurso.current) return
    envioEmCurso.current = true
    controle.current = new AbortController()
    definirEnviando(true)
    definirErro('')
    definirResultado(null)
    try {
      const retorno = await importarArquivos(arquivos.pedidos, arquivos.itens, controle.current.signal)
      definirResultado(retorno)
      aoImportar()
    } catch (falha) {
      if (falha.name !== 'AbortError') definirErro(falha.message)
=======
import { data } from "../servicos/formatacao";
import { useRef, useState } from "react";
import Cartao from "../componentes/Cartao";
import { api } from "../servicos/api";
import { Consulta, Tabela, Paginacao } from "../componentes/Elementos";
import "./Importacao.css";
export default function Importacao() {
  const [resultado, informar] = useState(null);
  const [erro, falhar] = useState("");
  const [ocupado, ocupar] = useState(false);
  const [versao, atualizar] = useState(0);
  const [pagina, paginar] = useState(1);
  const envio = useRef(false);
  async function importar(e) {
    e.preventDefault();
    if (envio.current) return;
    const form = new FormData(e.currentTarget);
    for (const campo of ["arquivo_cabecalho", "arquivo_itens"]) {
      const arq = form.get(campo);
      if (
        !arq?.size ||
        arq.size > 10 * 1024 * 1024 ||
        !/\.(xls|xlsx)$/i.test(arq.name)
      ) {
        falhar(
          "Selecione duas planilhas XLS/XLSX não vazias, de até 10 MB cada.",
        );
        return;
      }
    }
    envio.current = true;
    ocupar(true);
    falhar("");
    informar(null);
    try {
      const r = await api("/cargas/excel", { method: "POST", body: form });
      informar(r);
      atualizar(versao + 1);
      paginar(1);
    } catch (e) {
      falhar(e.message);
      atualizar(versao + 1);
>>>>>>> Stashed changes
    } finally {
      ocupar(false);
      envio.current = false;
    }
  }
  return (
<<<<<<< Updated upstream
    <main className="conteudo-painel tela-importacao" hidden={!ativa}>
      <header className="cabecalho-painel">
        <div>
          <p className="sobretitulo">DADOS COMERCIAIS</p>
          <h1 id="titulo-importacao" tabIndex={-1}>
            Importação de dados
          </h1>
          <p>Envie os relatórios de pedidos e produtos vendidos do mesmo período.</p>
        </div>
      </header>
      {podeImportar ? (
        <Cartao
          titulo="Importar planilhas Excel"
          descricao="XLS ou XLSX · até 10 MB por arquivo nesta interface."
        >
          <div className="grade-arquivos">
            {[
              {
                tipo: 'pedidos',
                titulo: '1. Pedidos',
                descricao: 'Planilha de pedidos e cabeçalho exportada do ERP.',
              },
              {
                tipo: 'itens',
                titulo: '2. Produtos vendidos',
                descricao: 'Planilha de itens faturados por produto.',
              },
            ].map(({ tipo, titulo, descricao }) => (
              <label
                className="area-arquivo"
                key={tipo}
                onDragOver={(evento) => evento.preventDefault()}
                onDrop={(evento) => {
                  evento.preventDefault()
                  selecionar(tipo, evento.dataTransfer.files)
                }}
              >
                <strong>{titulo}</strong>
                <span>{descricao}</span>
                <input
                  type="file"
                  accept=".xls,.xlsx"
                  disabled={enviando}
                  aria-label={titulo}
                  onChange={(evento) => selecionar(tipo, evento.target.files)}
                />
                <small>
                  {arquivos[tipo] ? arquivos[tipo].name : 'Selecione ou arraste a planilha para este campo.'}
                </small>
              </label>
            ))}
          </div>
          <p className="nota-informativa">
            Os arquivos serão enviados ao servidor e poderão atualizar os dados comerciais. Aguarde a
            confirmação antes de reenviar.
          </p>
          {erro && (
            <p className="erro-campo" role="alert">
              {erro}
            </p>
          )}
          <button
            className="botao-principal botao-importar"
            disabled={enviando || !arquivos.pedidos || !arquivos.itens}
            onClick={importar}
          >
            {enviando ? 'Importando…' : 'Importar dados'}
          </button>
          {enviando && (
            <p role="status">
              Processando os arquivos. O servidor pode levar alguns minutos; você pode continuar navegando.
            </p>
          )}
          {resultado && (
            <div role="status">
              <p>{resultado.mensagem || 'O servidor confirmou o recebimento da importação.'}</p>
              <div className="grade-indicadores indicadores-importacao">
                {[
                  { campo: 'pedidos', titulo: 'Pedidos processados' },
                  { campo: 'itens', titulo: 'Itens processados' },
                  { campo: 'adicionados', titulo: 'Pedidos novos' },
                  { campo: 'atualizados', titulo: 'Pedidos atualizados' },
                ]
                  .filter(({ campo }) => typeof resultado[campo] === 'number')
                  .map(({ campo, titulo }) => (
                    <CartaoIndicador key={campo} titulo={titulo} valor={resultado[campo]} />
                  ))}
              </div>
              {Array.isArray(resultado.avisos) &&
                resultado.avisos.map((aviso) => (
                  <p key={aviso} className="nota-informativa">
                    {aviso}
                  </p>
                ))}
            </div>
          )}
        </Cartao>
      ) : (
        <Cartao titulo="Importação restrita">
          <p>
            Seu perfil pode consultar os dados. Para importar arquivos, solicite acesso de administrador ou
            gestor.
          </p>
        </Cartao>
      )}
      <p className="nota-painel">
        Após a confirmação, os alertas e as próximas consultas de clientes serão atualizados. O histórico de
        importações ainda não está disponível.
      </p>
    </main>
  )
=======
    <>
      <Cartao
        titulo="Importar pedidos e produtos"
        descricao="Envie as duas planilhas do mesmo período. A carga inteira será validada antes de atualizar a base."
      >
        <form className="formulario-pagina" onSubmit={importar}>
          <label className="area-arquivo">
            <strong>1. Pedidos / cabeçalho</strong>
            <span>Identificação do cliente, fábrica, data e total</span>
            <input
              type="file"
              name="arquivo_cabecalho"
              accept=".xls,.xlsx"
              required
              disabled={ocupado}
            />
          </label>
          <label className="area-arquivo">
            <strong>2. Produtos vendidos / itens</strong>
            <span>Pedido, SKU, quantidade e preço</span>
            <input
              type="file"
              name="arquivo_itens"
              accept=".xls,.xlsx"
              required
              disabled={ocupado}
            />
          </label>
          <label>
            <input
              type="checkbox"
              name="permitir_atualizacao"
              value="true"
              disabled={ocupado}
            />{" "}
            Permitir atualizar pedidos existentes após conferir as duas
            planilhas
          </label>
          <small>
            Limite de 10 MB por arquivo. Não inclua pedidos incompletos.
            Reenvios idênticos não duplicam vendas.
          </small>
          <button className="botao-principal" disabled={ocupado}>
            {ocupado ? "Validando e importando…" : "Validar e importar"}
          </button>
        </form>
        {ocupado && (
          <p role="status">
            Aguarde a conclusão antes de reenviar os arquivos.
          </p>
        )}
        {erro && (
          <p className="erro-campo aviso" role="alert">
            {erro}
          </p>
        )}
        {resultado && (
          <div className="aviso" role="status">
            <strong>{resultado.mensagem}</strong>
            <p>
              {resultado.adicionados} pedidos adicionados ·{" "}
              {resultado.atualizados} atualizados · {resultado.inalterados}{" "}
              inalterados · {resultado.itens} itens
            </p>
          </div>
        )}
      </Cartao>
      <Cartao
        titulo="Layout aceito"
        descricao="Planilhas tabulares ou relatórios do ERP com cabeçalho e seções por produto."
      >
        <p>
          Pedidos: pedido, CNPJ/CPF, cliente, fábrica, data, valor total.
          Opcionais: vendedor, grupo, cidade, estado, micro região.
        </p>
        <p>
          Itens: pedido, SKU, nome do produto, quantidade, preço unitário.
          Opcionais: subtotal, categoria.
        </p>
        <p>
          Datas e valores inválidos, pedidos sem itens e divergências de totais
          impedem a carga. A fábrica deve ser identificada; não será criada uma
          associação automática à primeira fábrica.
        </p>
      </Cartao>
      <Cartao titulo="Histórico de importações">
        <Consulta caminho={`/cargas?pagina=${pagina}`} versao={versao}>
          {({ itens, total }) => (
            <>
              <Tabela
                colunas={[
                  "Arquivos",
                  "Data",
                  "Responsável",
                  "Situação",
                  "Detalhes",
                ]}
                linhas={itens.map((i) => [
                  i.arquivos,
                  data(i.criado_em),
                  i.usuario,
                  i.status,
                  <details>
                    <summary>Ver resultado</summary>
                    <p>{i.mensagem}</p>
                  </details>,
                ])}
                vazio="Nenhuma importação registrada."
              />
              <Paginacao pagina={pagina} total={total} aoMudar={paginar} />
            </>
          )}
        </Consulta>
      </Cartao>
    </>
  );
>>>>>>> Stashed changes
}
