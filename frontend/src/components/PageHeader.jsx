export default function PageHeader({
  eyebrow,
  title,
  description,
  action,
}) {
  return (
    <div className="mb-8 flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
      <div className="page-enter">
        <div className="mb-3 flex items-center gap-2">
          <span className="h-px w-6 bg-gradient-to-r from-indigo-400 to-fuchsia-400" />
          <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-indigo-300">
            {eyebrow}
          </p>
        </div>
        <h1 className="max-w-4xl bg-gradient-to-r from-white via-zinc-100 to-zinc-400 bg-clip-text text-3xl font-bold tracking-tight text-transparent sm:text-4xl">
          {title}
        </h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-zinc-400">
          {description}
        </p>
      </div>
      {action}
    </div>
  );
}
