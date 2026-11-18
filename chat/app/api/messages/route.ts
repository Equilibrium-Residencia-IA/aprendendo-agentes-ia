import { NextResponse } from "next/server";

type CreateMessageBody = {
  message?: unknown;
};

export async function POST(request: Request) {
  let body: CreateMessageBody;

  try {
    body = (await request.json()) as CreateMessageBody;
  } catch {
    return NextResponse.json(
      { error: "O corpo da requisição deve ser um JSON válido." },
      { status: 400 },
    );
  }

  if (typeof body.message !== "string" || body.message.trim().length === 0) {
    return NextResponse.json(
      { error: "Informe uma mensagem não vazia." },
      { status: 400 },
    );
  }

  const message = body.message.trim();

  if (message.length > 500) {
    return NextResponse.json(
      { error: "A mensagem deve ter no máximo 500 caracteres." },
      { status: 400 },
    );
  }

  return NextResponse.json(
    {
      id: crypto.randomUUID(),
      author: "Você",
      message,
    },
    { status: 201 },
  );
}
