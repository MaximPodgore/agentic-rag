import { Chat } from "./components/Chat";
import { FileDrop } from "./components/FileDrop";

export default function Home() {
  return (
    <div className="flex h-screen bg-zinc-50 dark:bg-zinc-950">
      <aside className="w-80 border-r border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 flex flex-col">
        <div className="p-4 border-b border-zinc-200 dark:border-zinc-800">
          <h1 className="text-lg font-bold text-zinc-900 dark:text-zinc-100">
            Agentic RAG
          </h1>
          <p className="text-xs text-zinc-500 mt-1">
            Ask questions about your documents
          </p>
        </div>
        <div className="flex-1 overflow-hidden">
          <FileDrop />
        </div>
      </aside>

      <main className="flex-1 flex flex-col">
        <Chat />
      </main>
    </div>
  );
}
