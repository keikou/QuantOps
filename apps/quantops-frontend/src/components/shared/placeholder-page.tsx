export function PlaceholderPage({ title, description }: { title: string; description: string }) {
  return (
    <div className="space-y-4">
      <h1 className="section-title">{title}</h1>
      <div className="card p-6 text-slate-300">{description}</div>
    </div>
  );
}
