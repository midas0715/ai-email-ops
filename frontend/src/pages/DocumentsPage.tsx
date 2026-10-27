import { useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { deleteDocument, listDocuments, uploadDocument } from "../api/org";
import { ErrorText } from "../components/ErrorText";
import { card, dangerButton, primaryButton } from "../components/styles";
import { formatDate, formatSize } from "../utils/format";

const DOCS_KEY = ["org", "documents"];
const MAX_BYTES = 5 * 1024 * 1024;
const ALLOWED = [".txt", ".pdf", ".docx"];

// Quick feedback before uploading. The server checks all of this again.
function checkFile(file: File): string | null {
  const name = file.name.toLowerCase();
  if (!ALLOWED.some((extension) => name.endsWith(extension))) {
    return "Only .txt, .pdf and .docx files are supported.";
  }
  if (file.size === 0) return "The file is empty.";
  if (file.size > MAX_BYTES) return "The file is larger than 5 MB.";
  return null;
}

function UploadForm() {
  const queryClient = useQueryClient();
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: uploadDocument,
    onSuccess: async () => {
      setFile(null);
      if (inputRef.current) inputRef.current.value = ""; // empty the file picker
      await queryClient.invalidateQueries({ queryKey: DOCS_KEY });
    },
  });

  return (
    <form
      className={`${card} space-y-4`}
      onSubmit={(event) => {
        event.preventDefault();
        if (file) mutation.mutate(file);
      }}
    >
      <h2 className="text-lg font-semibold">Upload a document</h2>
      <p className="text-sm text-slate-600">
        Text, PDF or Word files up to 5 MB. The AI uses them to draft replies. Scanned PDFs
        (pictures of text) cannot be read.
      </p>
      <input
        ref={inputRef}
        type="file"
        accept=".txt,.pdf,.docx"
        className="block w-full text-sm text-slate-600 file:mr-4 file:rounded-md file:border-0 file:bg-indigo-50 file:px-4 file:py-2 file:text-sm file:font-medium file:text-indigo-700 hover:file:bg-indigo-100"
        onChange={(event) => {
          const picked = event.target.files?.[0] ?? null;
          const problem = picked ? checkFile(picked) : null;
          mutation.reset();
          setFileError(problem);
          setFile(picked && !problem ? picked : null);
        }}
      />
      {fileError && (
        <p role="alert" className="text-sm text-red-600">
          {fileError}
        </p>
      )}
      <ErrorText error={mutation.error} />
      {mutation.isPending && (
        <p className="text-sm text-slate-500">
          Reading and indexing the document. The first upload can take a minute while the AI
          model loads.
        </p>
      )}
      <button type="submit" disabled={!file || mutation.isPending} className={primaryButton}>
        {mutation.isPending ? "Uploading..." : "Upload"}
      </button>
    </form>
  );
}

export function DocumentsPage() {
  const queryClient = useQueryClient();
  const documents = useQuery({ queryKey: DOCS_KEY, queryFn: listDocuments });

  const remove = useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: DOCS_KEY }),
  });

  return (
    <div className="space-y-8">
      <section>
        <h1 className="text-2xl font-semibold">Knowledge documents</h1>
        <p className="mt-1 text-sm text-slate-600">
          Policies, FAQs and guides that the AI can use when it drafts replies to customers.
        </p>
      </section>

      <UploadForm />

      <section className="space-y-3">
        {documents.isPending && <p className="text-slate-500">Loading...</p>}
        <ErrorText error={documents.error} />
        {documents.data && documents.data.length === 0 && (
          <p className="text-slate-500">No documents yet. Upload your first one above.</p>
        )}
        {documents.data && documents.data.length > 0 && (
          <div className={`${card} overflow-x-auto p-0`}>
            <table className="w-full text-left text-sm">
              <thead className="border-b border-slate-200 text-slate-500">
                <tr>
                  <th className="px-4 py-3 font-medium">File</th>
                  <th className="px-4 py-3 font-medium">Size</th>
                  <th className="px-4 py-3 font-medium">Chunks</th>
                  <th className="px-4 py-3 font-medium">Uploaded</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody>
                {documents.data.map((doc) => (
                  <tr key={doc.id} className="border-b border-slate-100 last:border-0">
                    <td className="px-4 py-3">{doc.filename}</td>
                    <td className="px-4 py-3 text-slate-600">{formatSize(doc.size_bytes)}</td>
                    <td className="px-4 py-3 text-slate-600">{doc.chunk_count}</td>
                    <td className="px-4 py-3 text-slate-600">{formatDate(doc.created_at)}</td>
                    <td className="px-4 py-3 text-right">
                      <button
                        className={dangerButton}
                        disabled={remove.isPending}
                        onClick={() => {
                          if (
                            window.confirm(
                              `Delete ${doc.filename}? The AI will no longer use it in replies.`,
                            )
                          ) {
                            remove.mutate(doc.id);
                          }
                        }}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <ErrorText error={remove.error} />
      </section>
    </div>
  );
}