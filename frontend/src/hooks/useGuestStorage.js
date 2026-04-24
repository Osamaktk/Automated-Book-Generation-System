import { useEffect, useState } from "react";

const DEFAULT_KEY = "guest_session_data";

function readInitialValue(storageKey, fallbackValue) {
  if (typeof window === "undefined") {
    return fallbackValue;
  }

  try {
    const rawValue = window.localStorage.getItem(storageKey);
    return rawValue ? JSON.parse(rawValue) : fallbackValue;
  } catch {
    return fallbackValue;
  }
}

export function useGuestStorage(initialValue, storageKey = DEFAULT_KEY) {
  const [value, setValue] = useState(() => readInitialValue(storageKey, initialValue));

  useEffect(() => {
    try {
      window.localStorage.setItem(storageKey, JSON.stringify(value));
    } catch {
      // Ignore localStorage write errors.
    }
  }, [storageKey, value]);

  function clearValue() {
    setValue(initialValue);
    try {
      window.localStorage.removeItem(storageKey);
    } catch {
      // Ignore localStorage removal errors.
    }
  }

  return [value, setValue, clearValue];
}
