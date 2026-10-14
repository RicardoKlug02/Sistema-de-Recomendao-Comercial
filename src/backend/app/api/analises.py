from datetime import date, timedelta
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from src.backend.app.api.deps import get_db, get_usuario_atual
from src.backend.app.services.analise_service import AnaliseService, hoje_comercial

router = APIRouter(prefix='/analises',tags=['Análise e relatórios de acompanhamento'],dependencies=[Depends(get_usuario_atual)])
Tipo = Literal['mapa','reativacoes','inativos','precos','regioes']


def servico(db,inicio,fim,vendedor_id,fabrica_id,rede):
    try:
        return AnaliseService(db,inicio,fim,vendedor_id,fabrica_id,rede)
    except ValueError as exc:
        raise HTTPException(422,str(exc))


@router.get('/impacto')
def impacto(implantacao: date = date(2026,9,29), fim: date | None = None,
            vendedor_id: int | None = None, fabrica_id: int | None = None,
            db: Session = Depends(get_db)):
    fim = fim or hoje_comercial()
    return servico(db,implantacao,fim,vendedor_id,fabrica_id,None).comparativo(implantacao,criterio='ciclo')


@router.get('/relatorios/{tipo}')
def relatorio(tipo: Tipo, inicio: date | None = None, fim: date | None = None,
              vendedor_id: int | None = None, fabrica_id: int | None = None, rede: str | None = None,
              status: Literal['Ativo','Inativo','Sem compra'] | None = None, codigo: str | None = None,
              escopo: Literal['cliente','fabrica'] = 'cliente', pagina: int = Query(1,ge=1),
              limite: int = Query(50,ge=1,le=200), db: Session = Depends(get_db)):
    fim=fim or hoje_comercial();inicio=inicio or fim-timedelta(days=29)
    dados=servico(db,inicio,fim,vendedor_id,fabrica_id,rede).relatorio(tipo,status,codigo,escopo)
    pos=(pagina-1)*limite
    return {**dados,'linhas':dados['linhas'][pos:pos+limite]}


@router.get('/relatorios/{tipo}/pdf')
def relatorio_pdf(tipo: Tipo, inicio: date | None = None, fim: date | None = None,
                  vendedor_id: int | None = None, fabrica_id: int | None = None, rede: str | None = None,
                  status: Literal['Ativo','Inativo','Sem compra'] | None = None, codigo: str | None = None,
                  escopo: Literal['cliente','fabrica'] = 'cliente', db: Session = Depends(get_db)):
    from src.backend.app.services.pdf_service import pdf_tabela
    fim=fim or hoje_comercial();inicio=inicio or fim-timedelta(days=29)
    dados=servico(db,inicio,fim,vendedor_id,fabrica_id,rede).relatorio(tipo,status,codigo,escopo)
    if dados['total']>5000:
        raise HTTPException(422,'O PDF excede 5.000 linhas. Selecione fábrica, rede, vendedor ou um período menor. A consulta na tela permanece completa e paginada.')
    return Response(pdf_tabela(dados),media_type='application/pdf',headers={
        'Content-Disposition':f'attachment; filename="relatorio-{tipo}.pdf"','Cache-Control':'no-store'})