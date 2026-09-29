import { useEffect, useState } from "react";
import { api } from "../servicos/api";
export default function useConsulta(caminho, versao = 0) {
  const [estado, definir] = useState({
    dados: null,
    erro: "",
    carregando: true,
  });
  useEffect(() => {
    const controller = new AbortController();
    api(caminho, { signal: controller.signal })
      .then((dados) => definir({ dados, erro: "", carregando: false }))
      .catch((e) => {
        if (e.name !== "AbortError")
          definir({ dados: null, erro: e.message, carregando: false });
      });
    return () => controller.abort();
  }, [caminho, versao]);
  return estado;
}
