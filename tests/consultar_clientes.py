import sys
from pathlib import Path

raiz = Path(__file__).resolve().parent.parent
if str(raiz) not in sys.path:
    sys.path.insert(0, str(raiz))

from sqlalchemy.orm import Session
from src.backend.app.core.database import engine
from src.backend.app.core.security import decrypt_data
from src.backend.app.models.cliente import Cliente
from src.backend.app.services.recomendacao_service import RecomendacaoService


def main():
    termo = sys.argv[1] if len(sys.argv) > 1 else input("Digite o nome ou parte da Razão Social do cliente: ")
    termo = termo.strip().lower()

    with Session(engine) as session:
        # 1. Varre clientes descriptografando para encontrar correspondências
        clientes = session.query(Cliente).all()
        correspondencias = []

        for c in clientes:
            nome = decrypt_data(c.razao_social) if c.razao_social else ""
            if termo in nome.lower():
                correspondencias.append((c, nome))

        if not correspondencias:
            print(f"\nNenhum cliente encontrado contendo '{termo}'.")
            return

        # 2. Seleção de cliente caso haja mais de um resultado
        if len(correspondencias) == 1:
            cliente_escolhido, nome_escolhido = correspondencias[0]
        else:
            print(f"\nForam encontrados {len(correspondencias)} clientes:")
            for idx, (c, nome) in enumerate(correspondencias, start=1):
                print(f"[{idx}] ID: {c.id:<5} | {nome:<45} | Rede: {c.grupo_economico}")
            
            escolha = int(input("\nDigite o número do cliente desejado: "))
            cliente_escolhido, nome_escolhido = correspondencias[escolha - 1]

        # 3. Consulta a Fachada para obter a Visão 360°
        service = RecomendacaoService(db_session=session)
        painel = service.obter_painel_visao_360(cliente_id=cliente_escolhido.id)

        print("\n" + "=" * 80)
        print(f"DOSSIÊ COMERCIAL 360°: {nome_escolhido.upper()}")
        print(f"ID: {painel['cliente_id']} | Rede/Grupo: {painel['grupo_economico']} | Cód. Analítico: {painel['codigo_analitico']}")
        print("=" * 80)

        # 4. Alertas de Recompra / Churn
        print("\n--- 1. ALERTAS DE RECOMPRA E CHURN ---")
        recompras = painel.get("alertas_recompra", [])
        if not recompras:
            print("Sem histórico suficiente para cálculo de ciclo de reposição.")
        else:
            for rec in recompras:
                print(f"★ [{rec['sku']}] {rec['nome']}")
                print(f"   Status: {rec['status']} | Atraso: {rec['dias_atraso']} dias")
                print(f"   Ciclo Médio: cada {rec['periodicidade_media_dias']} dias (Comprado {rec['total_compras_historico']}x)")
                print(f"   Previsão: {rec['previsao_proxima_compra']} | Volume Médio Habitual: {rec['volume_medio_pedido']} un.")
                print("-" * 60)

        # 5. Sugestões de Mix (Filtragem Colaborativa)
        print("\n--- 2. SUGESTÕES DE EXPANSÃO DE MIX ---")
        mix = painel.get("expansao_mix", [])
        if not mix:
            print("Nenhum item sugerido para expansão de mix no momento.")
        else:
            for item in mix:
                print(f"★ [{item['sku']}] {item['nome']}")
                print(f"   Afinidade: {item['afinidade_percentual']}% ({item['classificacao']})")
                print(f"   Sugestão de Pedido Inicial: {item['volume_sugerido_unidades']} un.")
                print(f"   Motivo: {item['motivo']}")
                print("-" * 60)

        # 6. Histórico recente de faturamento
        print("\n--- 3. ÚLTIMOS PEDIDOS FATURADOS ---")
        ultimos = painel.get("ultimos_pedidos", [])
        if not ultimos:
            print("Nenhum pedido recente registrado.")
        else:
            for ped in ultimos:
                data_formatada = ped['data'].strftime('%d/%m/%Y') if ped['data'] else "N/D"
                total = f"R$ {ped['total']:,.2f}" if ped['total'] else "R$ 0,00"
                print(f"• Pedido nº {ped['pedido']} | Data: {data_formatada} | Total: {total}")
        print("=" * 80 + "\n")


if __name__ == "__main__":
    main()