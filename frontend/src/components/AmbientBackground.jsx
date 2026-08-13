export default function AmbientBackground() {
  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      <div
        className="absolute -left-24 top-10 h-[420px] w-[420px] rounded-full bg-violet-600/10 blur-3xl"
        style={{ animation: "blobFloatOne 12s ease-in-out infinite" }}
      />
      <div
        className="absolute -right-28 top-1/4 h-[460px] w-[460px] rounded-full bg-cyan-500/10 blur-3xl"
        style={{ animation: "blobFloatTwo 14s ease-in-out infinite" }}
      />
      <div
        className="absolute bottom-[-120px] left-1/3 h-[440px] w-[440px] rounded-full bg-fuchsia-500/10 blur-3xl"
        style={{ animation: "blobFloatOne 16s ease-in-out infinite reverse" }}
      />
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,.018)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.018)_1px,transparent_1px)] bg-[size:42px_42px] [mask-image:linear-gradient(to_bottom,black,transparent_85%)]" />
    </div>
  );
}
