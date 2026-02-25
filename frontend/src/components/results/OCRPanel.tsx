interface OCRPanelProps {
  text: string;
}

export function OCRPanel({ text }: OCRPanelProps) {
  if (!text.trim()) {
    return null;
  }

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h3 className="text-lg font-semibold text-slate-900">Texto</h3>
      <pre className="mt-4 whitespace-pre-wrap text-sm leading-relaxed text-slate-700">{text}</pre>
    </section>
  );
}
