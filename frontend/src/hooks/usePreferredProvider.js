import { useEffect, useState } from "react";

export default function usePreferredProvider() {
  const [provider, setProvider] = useState(
    () => localStorage.getItem("preferred_provider") || "ollama",
  );

  useEffect(() => {
    localStorage.setItem("preferred_provider", provider);
  }, [provider]);

  return [provider, setProvider];
}
