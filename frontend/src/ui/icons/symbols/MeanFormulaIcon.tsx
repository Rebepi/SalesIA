import React from "react";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const MeanFormulaIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="fallback"
    renderPaths={() => (
      <g>
        <line x1="4" y1="4" x2="20" y2="4" />
        <path d="M7 20l5-12 5 12" />
        <line x1="9" y1="15" x2="15" y2="15" />
      </g>
    )}
  />
);
