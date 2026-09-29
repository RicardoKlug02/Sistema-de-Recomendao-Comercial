from collections import defaultdict, deque
from time import monotonic
from starlette.responses import JSONResponse


class LimiteUpload:
    """Limita o corpo antes de o parser multipart gravar arquivos temporários."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope.get("path") != "/api/v1/cargas/excel":
            return await self.app(scope, receive, send)
        limite = 21 * 1024 * 1024
        headers = dict(scope.get("headers", []))
        try:
            tamanho = int(headers.get(b"content-length", b"0"))
        except ValueError:
            tamanho = limite + 1
        if tamanho > limite:
            return await JSONResponse(
                {"detail": "Upload excede o limite de 21 MB por solicitação."},
                status_code=413,
            )(scope, receive, send)
        total = 0

        class Excesso(Exception):
            pass

        async def limitado():
            nonlocal total
            mensagem = await receive()
            total += len(mensagem.get("body", b""))
            if total > limite:
                raise Excesso()
            return mensagem

        try:
            await self.app(scope, limitado, send)
        except Excesso:
            await JSONResponse(
                {"detail": "Upload excede o limite de 21 MB por solicitação."},
                status_code=413,
            )(scope, receive, send)


class LimiteAutenticacao:
    """Proteção por processo. Distribuições com múltiplas instâncias precisam de limite no proxy."""

    def __init__(self, app):
        self.app = app
        self.eventos = defaultdict(deque)

    async def __call__(self, scope, receive, send):
        rotas = {
            "/api/v1/auth/login": 30,
            "/api/v1/auth/registrar": 10,
            "/api/v1/auth/recuperar": 10,
        }
        path = scope.get("path")
        if scope["type"] == "http" and scope.get("method") == "POST" and path in rotas:
            agora = monotonic()
            # Remover chaves expiradas para não acumular endereços indefinidamente.
            for chave in list(self.eventos):
                fila = self.eventos[chave]
                while fila and fila[0] < agora - 60:
                    fila.popleft()
                if not fila:
                    del self.eventos[chave]
            chave = (scope.get("client", ("desconhecido",))[0], path)
            fila = self.eventos[chave]
            if len(fila) >= rotas[path]:
                return await JSONResponse(
                    {"detail": "Muitas tentativas. Aguarde um minuto."},
                    status_code=429,
                    headers={"Retry-After": "60"},
                )(scope, receive, send)
            fila.append(agora)
        await self.app(scope, receive, send)
