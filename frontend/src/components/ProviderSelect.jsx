export default function ProviderSelect({ value, onChange, className = "" }) {
  return (
    <select
      className={`input ${className}`}
      value={value}
      onChange={(event) => onChange(event.target.value)}
    >
      <option value="ollama">Ollama · Local</option>
      <option value="gemini">Gemini · Cloud</option>
    </select>
  );
}
