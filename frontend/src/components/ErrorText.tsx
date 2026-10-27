export function ErrorText({ error }: { error: Error | null }) {
  if (!error) return null;
  return (
    <p role="alert" className="text-sm text-red-600">
      {error.message}
    </p>
  );
}