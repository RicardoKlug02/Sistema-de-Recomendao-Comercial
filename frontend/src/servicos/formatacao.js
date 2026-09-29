export const moeda = (valor) =>
  Number(valor || 0).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
export const data = (valor) =>
  valor
    ? new Date(`${valor.slice(0, 10)}T12:00:00`).toLocaleDateString("pt-BR")
    : "—";
