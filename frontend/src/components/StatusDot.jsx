export default function StatusDot({ online = true, label }) {
  return (
    <span className="badge">
      <span
        className={`h-2 w-2 rounded-full ${
          online ? "bg-emerald-400" : "bg-red-400"
        }`}
        style={online ? { animation: "pulseRing 2s infinite" } : undefined}
      />
      {label}
    </span>
  );
}
