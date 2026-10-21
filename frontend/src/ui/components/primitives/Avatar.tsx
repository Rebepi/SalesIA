import React from "react";

export const Avatar: React.FC<{ name: string; size?: "sm" | "md" | "lg" }> = ({
  name,
  size = "md"
}) => {
  const initials = name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .substring(0, 2)
    .toUpperCase();
  const sizeStyles = {
    sm: "w-7 h-7 text-xs",
    md: "w-9 h-9 text-sm",
    lg: "w-12 h-12 text-base font-bold"
  };
  return (
    <div
      aria-label={name}
      title={name}
      className={`rounded-full bg-blue-600/80 border border-blue-400/40 text-white flex items-center justify-center font-semibold select-none ${sizeStyles[size]}`}
    >
      {initials}
    </div>
  );
};
