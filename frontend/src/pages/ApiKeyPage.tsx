import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getOrgProfile } from "../api/auth";
import { createApiKey, revokeApiKey } from "../api/org";
import { ErrorText } from "../components/ErrorText";
import { card, dangerButton, primaryButton, secondaryButton } from "../components/styles";

const ORG_KEY = ["org", "me"];
const API_URL: string = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  return (
    <button
      type="button"
      className={secondaryButton}
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(text);
          setCopied(true);
          setTimeout(() => setCopied(false), 2000);
        } catch {
          // Clipboard access can be blocked. The key is still on screen to select by hand.
        }
      }}
    >
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

export function ApiKeyPage() {
  const queryClient = useQueryClient();
  const profile = useQuery({ queryKey: ORG_KEY, queryFn: getOrgProfile });

  const create = useMutation({
    mutationFn: createApiKey,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ORG_KEY }),
  });

  const revoke = useMutation({
    mutationFn: revokeApiKey,
    onSuccess: () => {
      create.reset(); // hide a freshly shown key once it has been revoked
      return queryClient.invalidateQueries({ queryKey: ORG_KEY });
    },
  });

  const hint = profile.data?.api_key_hint ?? null;
  const hasKey = hint !== null;

  return (
    <div className="space-y-8">
      <section>
        <h1 className="text-2xl font-semibold">API key for incoming emails</h1>
        <p className="mt-1 text-sm text-slate-600">
          Your email source (a website's server, a forwarding service or your own app) sends each
          email to the API with this key. The key tells the API which organization the email
          belongs to.
        </p>
      </section>

      <section className={`${card} space-y-4`}>
        {profile.isPending && <p className="text-slate-500">Loading...</p>}
        <ErrorText error={profile.error} />
        {profile.data && (
          <p className="text-sm">
            {hasKey ? (
              <>
                Status: <span className="font-medium text-green-700">active</span>, key ends in{" "}
                <code className="rounded bg-slate-100 px-1.5 py-0.5">{hint}</code>
              </>
            ) : (
              <>
                Status: <span className="font-medium text-slate-600">no key yet</span>. Emails
                cannot be delivered until you create one.
              </>
            )}
          </p>
        )}

        {create.data && (
          <div className="space-y-3 rounded-lg border border-amber-300 bg-amber-50 p-4">
            <p className="text-sm font-medium text-amber-900">
              Copy your new key now. It is shown only once, because the server keeps just a
              fingerprint of it.
            </p>
            <div className="flex items-center gap-3">
              <code className="flex-1 overflow-x-auto rounded bg-white px-3 py-2 text-sm">
                {create.data.api_key}
              </code>
              <CopyButton text={create.data.api_key} />
            </div>
          </div>
        )}

        <ErrorText error={create.error} />
        <ErrorText error={revoke.error} />

        <div className="flex flex-wrap gap-3">
          <button
            className={primaryButton}
            disabled={create.isPending || profile.isPending}
            onClick={() => {
              if (
                !hasKey ||
                window.confirm("Replace the key? The old key stops working immediately.")
              ) {
                create.mutate();
              }
            }}
          >
            {create.isPending ? "Creating..." : hasKey ? "Replace key" : "Create key"}
          </button>
          {hasKey && (
            <button
              className={dangerButton}
              disabled={revoke.isPending}
              onClick={() => {
                if (window.confirm("Revoke the key? Emails will be rejected until you create a new one.")) {
                  revoke.mutate();
                }
              }}
            >
              Revoke key
            </button>
          )}
        </div>
      </section>

      <section className={`${card} space-y-3`}>
        <h2 className="text-lg font-semibold">How to send an email</h2>
        <pre className="overflow-x-auto rounded bg-slate-900 p-4 text-sm text-slate-100">
          {`POST ${API_URL}/inbound/emails
X-API-Key: <your key>
Content-Type: application/json

{ "sender_email": "customer@example.com", "subject": "Hello", "body": "Message text" }`}
        </pre>
        <p className="text-sm text-slate-600">
          Keep the key on a server. Never put it in a web page's JavaScript, because anyone who
          opens the page could read it.
        </p>
      </section>
    </div>
  );
}