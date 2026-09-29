<<<<<<< Updated upstream
import { useEffect, useRef, useState } from 'react'
import CartaoAutenticacao from './componentes/CartaoAutenticacao'
import FormularioAutenticacao from './componentes/FormularioAutenticacao'
import PainelComercial from './paginas/PainelComercial'
import { encerrarSessao, obterSessao } from './servicos/api'
import './Autenticacao.css'

export default function Aplicacao() {
  const [usuario, definirUsuario] = useState(() => obterSessao()?.usuario || null)
  const [mensagem, definirMensagem] = useState('')
  const referenciaTitulo = useRef(null)
  useEffect(() => {
    function expirar() {
      definirUsuario(null)
      definirMensagem('Sua sessão expirou. Entre novamente para continuar.')
    }
    window.addEventListener('sessao-expirada', expirar)
    return () => window.removeEventListener('sessao-expirada', expirar)
  }, [])
  useEffect(() => {
    if (!usuario) {
      document.title = 'Login | Rio Verde Representações'
      referenciaTitulo.current?.focus()
    }
  }, [usuario])
  function sair() {
    encerrarSessao()
    definirUsuario(null)
    definirMensagem('')
  }
  if (usuario) return <PainelComercial usuario={usuario} aoSair={sair} />
  return (
    <main className="pagina-autenticacao">
      <CartaoAutenticacao
        titulo="Acesse sua carteira."
        subtitulo="Entre com sua conta para acompanhar os dados comerciais."
        referenciaTitulo={referenciaTitulo}
      >
        {mensagem && (
          <p className="erro-campo" role="alert">
            {mensagem}
          </p>
        )}
        <FormularioAutenticacao aoEntrar={definirUsuario} />
      </CartaoAutenticacao>
    </main>
  )
=======
import { useEffect, useRef, useState } from "react";
import MenuLateral from "./componentes/MenuLateral";
import Acesso from "./paginas/Acesso";
import { Clientes, FichaCliente } from "./paginas/Clientes";
import {
  Painel,
  Alertas,
  Oportunidades,
  Relatorios,
} from "./paginas/Comercial";
import { Usuarios, Perfil } from "./paginas/Conta";
import Importacao from "./paginas/Importacao";
import { definirToken } from "./servicos/api";
import "./Autenticacao.css";
import "./paginas/PainelComercial.css";
import "./paginas/Sistema.css";
const lerRota = () => window.location.hash.replace(/^#\/?/, "") || "painel";
const nomes = {
  painel: "Visão geral",
  clientes: "Clientes",
  oportunidades: "Oportunidades",
  alertas: "Alertas de recompra",
  relatorios: "Relatórios",
  importacoes: "Importação de dados",
  usuarios: "Usuários",
  perfil: "Minha conta",
};
export default function Aplicacao() {
  const [rota, navegar] = useState(lerRota);
  const [usuario, autenticar] = useState(null);
  const [aviso, avisar] = useState("");
  const titulo = useRef(null);
  useEffect(() => {
    const mudou = () => navegar(lerRota());
    const expirou = () => {
      autenticar(null);
      avisar("Sua sessão expirou. Entre novamente.");
      window.location.hash = "/entrar";
    };
    window.addEventListener("hashchange", mudou);
    window.addEventListener("sessao-expirada", expirou);
    return () => {
      window.removeEventListener("hashchange", mudou);
      window.removeEventListener("sessao-expirada", expirou);
    };
  }, []);
  const [secao, id] = rota.split("/");
  useEffect(() => {
    document.title = `${nomes[secao] || "Acesso"} | Rio Verde`;
    titulo.current?.focus();
  }, [secao, id, usuario]);
  function sair() {
    definirToken(null);
    autenticar(null);
    avisar("");
    window.location.hash = "/entrar";
  }
  const publica = ["entrar", "cadastro", "recuperar", "redefinir"].includes(
    secao.split("?")[0],
  );
  if (!usuario)
    return (
      <Acesso
        key={rota}
        rota={publica ? rota : "entrar"}
        aviso={aviso}
        aoEntrar={(u) => {
          autenticar(u);
          avisar("");
          if (publica) window.location.hash = "/painel";
        }}
      />
    );
  const admin = ["admin", "gestor"].includes(usuario.perfil);
  let conteudo;
  if (["usuarios", "importacoes"].includes(secao) && !admin)
    conteudo = (
      <div role="alert" className="estado-vazio">
        Acesso restrito aos gestores.
      </div>
    );
  else if (secao === "clientes")
    conteudo = id ? <FichaCliente key={id} id={id} /> : <Clientes />;
  else
    conteudo = {
      painel: <Painel />,
      oportunidades: <Oportunidades />,
      alertas: <Alertas />,
      relatorios: <Relatorios />,
      importacoes: <Importacao />,
      usuarios: <Usuarios usuario={usuario} />,
      perfil: <Perfil usuario={usuario} aoSair={sair} />,
    }[secao];
  return (
    <div className="estrutura-painel">
      <a
        className="atalho-conteudo"
        href="#conteudo"
        onClick={(e) => {
          e.preventDefault();
          titulo.current?.focus();
        }}
      >
        Pular para o conteúdo
      </a>
      <MenuLateral usuario={usuario} secaoAtiva={secao} aoSair={sair} />
      <main className="conteudo-painel">
        <header className="cabecalho-painel">
          <div>
            <p className="sobretitulo">RIO VERDE · COMERCIAL</p>
            <h1 id="conteudo" ref={titulo} tabIndex={-1}>
              {id && secao === "clientes"
                ? "Perfil do cliente"
                : nomes[secao] || "Página não encontrada"}
            </h1>
            <p>Informação para transformar sua próxima conversa.</p>
          </div>
          <span className="aviso-demonstracao">
            {new Date().toLocaleDateString("pt-BR", {
              day: "numeric",
              month: "long",
              year: "numeric",
            })}
          </span>
        </header>
        <div key={rota} className="pilha-pagina">
          {conteudo || (
            <div className="estado-vazio">
              <p>Esta página não existe.</p>
              <a href="#/painel">Voltar ao início</a>
            </div>
          )}
        </div>
      </main>
    </div>
  );
>>>>>>> Stashed changes
}
