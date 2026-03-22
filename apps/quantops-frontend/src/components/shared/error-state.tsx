export function ErrorState({ message }: { message: string }) {
  return <div className="card border-red-900 bg-red-950/20 p-6 text-red-300">{message}</div>;
}
