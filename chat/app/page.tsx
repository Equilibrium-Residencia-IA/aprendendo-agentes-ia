"use client";

import { FormEvent, useState } from "react";
import {
  Avatar,
  AvatarFallback,
} from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Bubble, BubbleContent } from "@/components/ui/bubble";
import {
  Message,
  MessageAvatar,
  MessageContent,
  MessageHeader,
} from "@/components/ui/message";
import {
  MessageScroller,
  MessageScrollerButton,
  MessageScrollerContent,
  MessageScrollerItem,
  MessageScrollerProvider,
  MessageScrollerViewport,
} from "@/components/ui/message-scroller";

type Message = {
  id: string;
  author: string;
  message: string;
};

const initialMessages: Message[] = [
  {
    id: "message-1",
    author: "Ana",
    message: "Oi! Como está o andamento do projeto?",
  },
  {
    id: "message-2",
    author: "Você",
    message: "Está indo bem. Terminei a integração do novo componente.",
  },
  {
    id: "message-3",
    author: "Ana",
    message: "Perfeito! Podemos revisar juntos mais tarde.",
  },
  {
    id: "message-4",
    author: "Você",
    message: "Combinado. Vou deixar tudo preparado.",
  },
];

export default function Home() {
  const [messages, setMessages] = useState(initialMessages);
  const [message, setMessage] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = message.trim();

    if (!text || isSending) {
      return;
    }

    setIsSending(true);
    setError(null);

    try {
      const response = await fetch("/api/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      const data = (await response.json()) as Message | { error?: string };

      if (!response.ok || !("id" in data)) {
        throw new Error(
          "error" in data && data.error
            ? data.error
            : "Não foi possível enviar a mensagem.",
        );
      }

      setMessages((currentMessages) => [...currentMessages, data]);
      setMessage("");
    } catch (submitError) {
      setError(
        submitError instanceof Error
          ? submitError.message
          : "Não foi possível enviar a mensagem.",
      );
    } finally {
      setIsSending(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-muted/40 p-6">
      <section className="flex h-[min(42rem,calc(100vh-3rem))] w-full max-w-2xl flex-col overflow-hidden rounded-xl border bg-background shadow-sm">
        <header className="border-b px-6 py-4">
          <h1 className="font-semibold">Mensagens</h1>
          <p className="text-sm text-muted-foreground">
            Um exemplo usando o Message Scroller do shadcn.
          </p>
        </header>

        <MessageScrollerProvider autoScroll defaultScrollPosition="end">
          <MessageScroller className="flex-1">
            <MessageScrollerViewport aria-label="Histórico de mensagens">
              <MessageScrollerContent className="p-6">
                {messages.map((item) => (
                  <MessageScrollerItem
                    key={item.id}
                    messageId={item.id}
                    scrollAnchor={item.author === "Você"}
                  >
                    <Message align={item.author === "Você" ? "end" : "start"}>
                      <MessageAvatar>
                        <Avatar>
                          <AvatarFallback>
                            {item.author.slice(0, 1)}
                          </AvatarFallback>
                        </Avatar>
                      </MessageAvatar>
                      <MessageContent>
                        <MessageHeader>{item.author}</MessageHeader>
                        <Bubble
                          align={item.author === "Você" ? "end" : "start"}
                          variant={
                            item.author === "Você" ? "default" : "secondary"
                          }
                        >
                          <BubbleContent>{item.message}</BubbleContent>
                        </Bubble>
                      </MessageContent>
                    </Message>
                  </MessageScrollerItem>
                ))}
              </MessageScrollerContent>
            </MessageScrollerViewport>
            <MessageScrollerButton aria-label="Ir para o fim" />
          </MessageScroller>
        </MessageScrollerProvider>

        <form className="flex gap-2 border-t p-4" onSubmit={handleSubmit}>
          <input
            aria-label="Nova mensagem"
            className="min-w-0 flex-1 rounded-lg border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
            maxLength={500}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="Escreva uma mensagem..."
            value={message}
          />
          <Button
            disabled={isSending || message.trim().length === 0}
            type="submit"
          >
            {isSending ? "Enviando..." : "Enviar"}
          </Button>
        </form>
        {error ? (
          <p className="px-4 pb-4 text-sm text-destructive" role="alert">
            {error}
          </p>
        ) : null}
      </section>
    </main>
  );
}
