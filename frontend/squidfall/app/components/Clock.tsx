"use client";

import { useEffect, useState } from "react";

export function Clock() {
  const [now, setNow] = useState<string>("");

  useEffect(() => {
    const tick = () =>
      setNow(
        new Date().toLocaleTimeString("en-US", {
          hour12: false,
          timeZone: "UTC",
        }) + " UTC"
      );
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <span className="clock" suppressHydrationWarning>
      {now}
    </span>
  );
}
