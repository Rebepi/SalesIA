import React from "react";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const CompanyIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="fallback"
    renderPaths={() => (
      <g>
        <path d="M3 21h18" />
        <path d="M5 21V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16" />
        <path d="M9 7h1" />
        <path d="M9 11h1" />
        <path d="M9 15h1" />
        <path d="M14 7h1" />
        <path d="M14 11h1" />
        <path d="M14 15h1" />
      </g>
    )}
  />
);
