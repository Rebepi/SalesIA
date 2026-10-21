import React from "react";
import type { IconProps } from "./AnimatedIconBase";
import { AnimatedIconBase } from "./AnimatedIconBase";

export const BayesProbabilityIcon: React.FC<IconProps> = (props) => (
  <AnimatedIconBase
    {...props}
    iconId="fallback"
    renderPaths={() => (
      <g>
        <circle cx="9" cy="12" r="6" />
        <circle cx="15" cy="12" r="6" />
      </g>
    )}
  />
);
