import { useState } from "react";
import { FileUp, Search, Sparkles, Database, FileText } from "lucide-react";
import { api } from "../lib/api";
import PageHeader from "../components/PageHeader";
import ResultCard from "../components/ResultCard";
import ProviderSelect from "../components/ProviderSelect";
import usePreferredProvider from "../hooks/usePreferredProvider";

export default function Documents() {
  const [file, setFile] = useState(null);
  const [documentId, setDocumentId] = useState("");
  const [query, setQuery] = useState("");
  const [provider, setProvider] = usePreferredProvider();
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function run(action) {
    setLoading(true);
    setError("");
    setResult(null);

    try {
      let data;

      if (action === "upload") {
        if (!file) throw new Error("Choose a PDF or TXT file first.");
        const formData = new FormData();
        formData.append("file", file);
        data = await api.upload("/documents/upload", formData);
        if (data?.document_id) setDocumentId(data.document_id);
      }

      if (action === "index") {
        if (!documentId) throw new Error("Document ID is required.");
        data = await api.post(`/documents/${documentId}/index`, {});
      }

      if (action === "analyze") {
        if (!documentId) throw new Error("Document ID is required.");
        data = await api.post(
          `/document-analysis/${documentId}/analyze`,
          { provider },
        );
      }

      if (action === "search") {
        if (!query.trim()) throw new Error("Enter a search query.");
        data = await api.post("/search", {
          query,
          top_k: 5,
          document_id: documentId || null,
        });
      }

      setResult(data);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="Knowledge Intelligence"
        title="Turn documents into decisions"
        description="Upload, index, search and analyze workplace knowledge using your RAG pipeline and AI Document Analyzer."
      />

      <div className="grid gap-6 xl:grid-cols-[1.05fr_.95fr]">
        <section className="panel-hover shine p-5 sm:p-6">
          <div className="mb-6 flex items-center gap-3">
            <div className="grid h-11 w-11 place-items-center rounded-2xl bg-indigo-500/10 text-indigo-300">
              <FileText size={20} />
            </div>
            <div>
              <h2 className="font-semibold">Document workspace</h2>
              <p className="text-xs text-zinc-500">PDF and TXT intelligence</p>
            </div>
          </div>

          <label className="label">File</label>
          <label className="mb-5 flex min-h-32 cursor-pointer flex-col items-center justify-center rounded-3xl border border-dashed border-white/15 bg-black/15 p-5 text-center transition hover:border-indigo-400/40 hover:bg-indigo-500/[0.035]">
            <FileUp size={24} className="mb-3 text-indigo-300" />
            <span className="text-sm font-medium text-zinc-300">
              {file ? file.name : "Drop or choose a document"}
            </span>
            <span className="mt-1 text-xs text-zinc-600">PDF or TXT</span>
            <input
              className="hidden"
              type="file"
              accept=".pdf,.txt,application/pdf,text/plain"
              onChange={(event) => setFile(event.target.files?.[0] || null)}
            />
          </label>

          <button
            className="btn-primary mb-6"
            onClick={() => run("upload")}
            disabled={loading}
          >
            <FileUp size={17} />
            Upload
          </button>

          <label className="label">Document ID</label>
          <input
            className="input mb-4 font-mono text-xs"
            value={documentId}
            onChange={(event) => setDocumentId(event.target.value)}
            placeholder="Document UUID"
          />

          <label className="label">AI Provider</label>
          <ProviderSelect
            className="mb-5"
            value={provider}
            onChange={setProvider}
          />

          <div className="flex flex-wrap gap-3">
            <button
              className="btn-secondary"
              disabled={!documentId || loading}
              onClick={() => run("index")}
            >
              <Database size={16} />
              Index
            </button>
            <button
              className="btn-primary"
              disabled={!documentId || loading}
              onClick={() => run("analyze")}
            >
              <Sparkles size={17} />
              Analyze
            </button>
          </div>
        </section>

        <section className="panel-hover p-5 sm:p-6">
          <div className="mb-6 flex items-center gap-3">
            <div className="grid h-11 w-11 place-items-center rounded-2xl bg-cyan-500/10 text-cyan-300">
              <Search size={20} />
            </div>
            <div>
              <h2 className="font-semibold">Knowledge search</h2>
              <p className="text-xs text-zinc-500">Semantic retrieval over indexed chunks</p>
            </div>
          </div>

          <label className="label">Search query</label>
          <textarea
            className="input min-h-44 resize-none"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="What does our handbook say about incident response?"
          />

          <button
            className="btn-primary mt-4"
            disabled={!query.trim() || loading}
            onClick={() => run("search")}
          >
            <Search size={17} />
            Search company knowledge
          </button>

          <div className="mt-8 rounded-2xl border border-white/[0.07] bg-white/[0.025] p-4">
            <p className="text-xs font-semibold text-zinc-400">Tip</p>
            <p className="mt-2 text-xs leading-5 text-zinc-600">
              Leave Document ID empty to search across all indexed company documents.
            </p>
          </div>
        </section>
      </div>

      <div className="mt-6">
        <ResultCard
          title="Document intelligence"
          result={result}
          error={error}
          loading={loading}
        />
      </div>
    </>
  );
}
